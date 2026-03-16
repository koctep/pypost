"""MCP client service for testing MCP endpoints via full protocol handshake."""
import asyncio
import json
import time
from typing import Any

from mcp.client.sse import sse_client
from mcp.client.session import ClientSession

from pypost.models.response import ResponseData

MCP_CONNECT_TIMEOUT = 3.0
MCP_SSE_READ_TIMEOUT = 10.0
MCP_TOTAL_TIMEOUT = 25.0


class MCPClientService:
    """Sync wrapper around async MCP client for list_tools and call_tool."""

    def run(
        self,
        url: str,
        operation: str,
        call_params: dict[str, Any] | None = None,
    ) -> ResponseData:
        """
        Run MCP operation (list_tools or call_tool) against the given SSE endpoint.

        Args:
            url: MCP SSE endpoint URL (e.g. http://localhost:1080/sse).
            operation: "list_tools" or "call_tool".
            call_params: For call_tool, {"name": str, "arguments": dict}.

        Returns:
            ResponseData with JSON body (tools list or call result) or error message.
        """
        start_time = time.time()
        try:
            result = asyncio.run(
                asyncio.wait_for(
                    self._run_async(url, operation, call_params or {}),
                    timeout=MCP_TOTAL_TIMEOUT,
                )
            )
        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            err_body = json.dumps(
                {
                    "error": f"Timeout after {MCP_TOTAL_TIMEOUT}s",
                    "hint": (
                        "Ensure MCP server is running (enable_mcp in environment) "
                        "and reachable at the given URL."
                    ),
                }
            )
            return ResponseData(
                status_code=504,
                headers={},
                body=err_body,
                elapsed_time=elapsed,
                size=len(err_body.encode("utf-8")),
            )
        except Exception as e:
            elapsed = time.time() - start_time
            err_msg = str(e)
            if isinstance(e, BaseExceptionGroup):
                err_msg = "; ".join(str(x) for x in e.exceptions)
            hint = ""
            err_type = type(e).__name__
            if "ConnectError" in err_type or "connection" in err_msg.lower():
                hint = " Is the MCP server running? Select environment with enable_mcp."
            elif "Timeout" in err_type or "timeout" in err_msg.lower():
                hint = (
                    " Server may not send endpoint event. Check server is MCP SSE "
                    "compatible."
                )
            body = json.dumps(
                {"error": err_msg, "hint": hint} if hint else {"error": err_msg}
            )
            return ResponseData(
                status_code=500,
                headers={},
                body=body,
                elapsed_time=elapsed,
                size=len(body.encode("utf-8")),
            )

        elapsed = time.time() - start_time
        body_str = result if isinstance(result, str) else json.dumps(result)
        return ResponseData(
            status_code=200,
            headers={"Content-Type": "application/json"},
            body=body_str,
            elapsed_time=elapsed,
            size=len(body_str.encode("utf-8")),
        )

    async def _run_async(
        self,
        url: str,
        operation: str,
        call_params: dict[str, Any],
    ) -> str | dict:
        async with sse_client(
            url,
            timeout=MCP_CONNECT_TIMEOUT,
            sse_read_timeout=MCP_SSE_READ_TIMEOUT,
        ) as (read_stream, write_stream):
            session = ClientSession(read_stream, write_stream)
            await session.initialize()

            if operation == "list_tools":
                result = await session.list_tools()
                return result.model_dump(mode="json")
            elif operation == "call_tool":
                name = call_params.get("name")
                if not name:
                    raise ValueError("call_tool requires 'name' in body")
                arguments = call_params.get("arguments") or {}
                result = await session.call_tool(name, arguments)
                return result.model_dump(mode="json")
            else:
                raise ValueError(f"Unknown operation: {operation}")
