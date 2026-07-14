"""MCP client service for testing MCP endpoints via full protocol handshake."""
from __future__ import annotations

import json
import logging
import time
from typing import Any

import anyio
import httpx
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.shared._httpx_utils import create_mcp_http_client

from pypost.models.errors import ErrorCategory, ExecutionError
from pypost.models.response import ResponseData

logger = logging.getLogger(__name__)

MCP_CONNECT_TIMEOUT = 3.0
MCP_READ_TIMEOUT = 10.0
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
        Run MCP operation (list_tools or call_tool) against the given MCP endpoint.

        Args:
            url: Streamable HTTP MCP URL (e.g. http://localhost:1080/mcp).
            operation: "list_tools" or "call_tool".
            call_params: For call_tool, {"name": str, "arguments": dict}.

        Returns:
            ResponseData with JSON body (tools list or call result) or error message.
        """
        start_time = time.time()
        logger.debug("mcp_operation_start url=%s operation=%s", url, operation)
        try:
            result = anyio.run(
                self._run_with_timeout,
                url,
                operation,
                call_params or {},
            )
        except TimeoutError as exc:
            logger.error(
                "mcp_operation_timeout url=%s operation=%s timeout=%.1f",
                url,
                operation,
                MCP_TOTAL_TIMEOUT,
            )
            raise ExecutionError(
                category=ErrorCategory.TIMEOUT,
                message=f"MCP request timed out after {MCP_TOTAL_TIMEOUT}s.",
                detail=str(exc),
            ) from exc
        except httpx.TimeoutException as exc:
            logger.error(
                "mcp_operation_failed url=%s operation=%s category=%s detail=%s",
                url,
                operation,
                ErrorCategory.TIMEOUT,
                exc,
            )
            raise ExecutionError(
                category=ErrorCategory.TIMEOUT,
                message="MCP server did not respond in time.",
                detail=str(exc),
            ) from exc
        except httpx.NetworkError as exc:
            logger.error(
                "mcp_operation_failed url=%s operation=%s category=%s detail=%s",
                url,
                operation,
                ErrorCategory.NETWORK,
                exc,
            )
            raise ExecutionError(
                category=ErrorCategory.NETWORK,
                message="Could not connect to MCP server. Is it running?",
                detail=str(exc),
            ) from exc
        except httpx.RequestError as exc:
            logger.error(
                "mcp_operation_failed url=%s operation=%s category=%s detail=%s",
                url,
                operation,
                ErrorCategory.UNKNOWN,
                exc,
            )
            raise ExecutionError(
                category=ErrorCategory.UNKNOWN,
                message="MCP operation failed.",
                detail=str(exc),
            ) from exc
        except Exception as exc:
            err_msg = str(exc)
            if isinstance(exc, BaseExceptionGroup):
                err_msg = "; ".join(str(x) for x in exc.exceptions)
            logger.error(
                "mcp_operation_failed url=%s operation=%s category=%s detail=%s",
                url,
                operation,
                ErrorCategory.UNKNOWN,
                err_msg,
            )
            raise ExecutionError(
                category=ErrorCategory.UNKNOWN,
                message="MCP operation failed.",
                detail=err_msg,
            ) from exc

        elapsed = time.time() - start_time
        logger.debug(
            "mcp_operation_success url=%s operation=%s elapsed=%.3f", url, operation, elapsed
        )
        body_str = result if isinstance(result, str) else json.dumps(result)
        return ResponseData(
            status_code=200,
            headers={"Content-Type": "application/json"},
            body=body_str,
            elapsed_time=elapsed,
            size=len(body_str.encode("utf-8")),
        )

    async def _run_with_timeout(
        self,
        url: str,
        operation: str,
        call_params: dict[str, Any],
    ) -> str | dict:
        with anyio.fail_after(MCP_TOTAL_TIMEOUT):
            return await self._run_async(url, operation, call_params)

    async def _run_async(
        self,
        url: str,
        operation: str,
        call_params: dict[str, Any],
    ) -> str | dict:
        timeout = httpx.Timeout(MCP_CONNECT_TIMEOUT, read=MCP_READ_TIMEOUT)
        async with create_mcp_http_client(timeout=timeout) as http_client:
            async with streamable_http_client(
                url, http_client=http_client
            ) as (read_stream, write_stream, _get_session_id):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()

                    if operation == "list_tools":
                        result = await session.list_tools()
                        return result.model_dump(mode="json")
                    if operation == "call_tool":
                        name = call_params.get("name")
                        if not name:
                            raise ValueError("call_tool requires 'name' in body")
                        arguments = call_params.get("arguments") or {}
                        result = await session.call_tool(name, arguments)
                        return result.model_dump(mode="json")
                    raise ValueError(f"Unknown operation: {operation}")
