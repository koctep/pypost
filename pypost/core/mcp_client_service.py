"""MCP client service for testing MCP endpoints via full protocol handshake."""
import asyncio
import json
import logging
import time
from typing import Any

from mcp.client.sse import sse_client
from mcp.client.session import ClientSession

from pypost.models.response import ResponseData
from pypost.models.errors import ErrorCategory, ExecutionError

logger = logging.getLogger(__name__)

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
        logger.debug("mcp_operation_start url=%s operation=%s", url, operation)
        try:
            result = asyncio.run(
                asyncio.wait_for(
                    self._run_async(url, operation, call_params or {}),
                    timeout=MCP_TOTAL_TIMEOUT,
                )
            )
        except asyncio.TimeoutError as exc:
            logger.error(
                "mcp_operation_timeout url=%s operation=%s timeout=%.1f",
                url, operation, MCP_TOTAL_TIMEOUT,
            )
            raise ExecutionError(
                category=ErrorCategory.TIMEOUT,
                message=f"MCP request timed out after {MCP_TOTAL_TIMEOUT}s.",
                detail=str(exc),
            ) from exc
        except Exception as exc:
            err_msg = str(exc)
            if isinstance(exc, BaseExceptionGroup):
                err_msg = "; ".join(str(x) for x in exc.exceptions)
            err_type = type(exc).__name__
            if "ConnectError" in err_type or "connection" in err_msg.lower():
                category = ErrorCategory.NETWORK
                message = "Could not connect to MCP server. Is it running?"
            elif "Timeout" in err_type or "timeout" in err_msg.lower():
                category = ErrorCategory.TIMEOUT
                message = "MCP server did not respond in time."
            else:
                category = ErrorCategory.UNKNOWN
                message = "MCP operation failed."
            logger.error(
                "mcp_operation_failed url=%s operation=%s category=%s detail=%s",
                url, operation, category, err_msg,
            )
            raise ExecutionError(category=category, message=message, detail=err_msg) from exc

        elapsed = time.time() - start_time
        logger.debug("mcp_operation_success url=%s operation=%s elapsed=%.3f", url, operation, elapsed)
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
