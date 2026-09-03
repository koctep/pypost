"""Transparent MCP Reverse Proxy implementation.

Forwards standard MCP protocol operations (tools, prompts, resources) to
an external upstream MCP server with dynamic environment variable header resolution.
"""
from __future__ import annotations

import contextlib
import logging
import time
import uuid
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from typing import Any, Literal, cast

import httpx
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamable_http_client
from mcp.server import Server
from mcp.shared._httpx_utils import create_mcp_http_client
from starlette.applications import Starlette
from starlette.routing import Mount

from pypost.core.mcp_activity_log import McpActivityEntry, McpActivityLog
from pypost.core.mcp_legacy_sse import build_legacy_sse_app
from pypost.core.mcp_proxy_headers import (
    McpUnresolvedVariableError,
    resolve_proxy_headers,
    sanitize_proxy_headers,
)
from pypost.core.mcp_streamable_http import build_streamable_http_route
from pypost.core.mcp_transport_routes import MCP_LEGACY_SSE_MOUNT_PATH
from pypost.core.metrics_protocol import MetricsTrackerProtocol, resolve_metrics
from pypost.core.template_service import TemplateService

logger = logging.getLogger(__name__)


class MCPProxyServerImpl:
    """MCP Reverse Proxy server that forwards protocol requests to an upstream target."""

    def __init__(
        self,
        name: str = "pypost-proxy",
        upstream_url: str = "",
        upstream_transport: Literal["streamable_http", "sse"] = "streamable_http",
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
        variable_supplier: Callable[[], dict[str, str]] | None = None,
        hidden_keys_supplier: Callable[[], set[str]] | None = None,
        activity_log: McpActivityLog | None = None,
        metrics: MetricsTrackerProtocol | None = None,
        template_service: TemplateService | None = None,
    ) -> None:
        self.name = name
        self.upstream_url = upstream_url
        self.upstream_transport = upstream_transport
        self.headers = dict(headers or {})
        self.timeout = timeout
        self._variable_supplier = variable_supplier or (lambda: {})
        self._hidden_keys_supplier = hidden_keys_supplier or (lambda: set())
        self._activity_log = activity_log
        self._metrics = resolve_metrics(metrics)
        self._template_service = template_service

        self.server = Server(name)

        # Register MCP protocol handlers
        self.server.list_tools()(self.list_tools)
        self.server.call_tool()(self.call_tool)
        self.server.list_prompts()(self.list_prompts)
        self.server.get_prompt()(self.get_prompt)
        self.server.list_resources()(self.list_resources)
        self.server.read_resource()(self.read_resource)

    def set_variable_supplier(
        self, supplier: Callable[[], dict[str, str]] | None
    ) -> None:
        self._variable_supplier = supplier or (lambda: {})

    def set_hidden_keys_supplier(
        self, supplier: Callable[[], set[str]] | None
    ) -> None:
        self._hidden_keys_supplier = supplier or (lambda: set())

    def _resolve_headers(self) -> dict[str, str]:
        env_vars = self._variable_supplier()
        try:
            return resolve_proxy_headers(
                self.headers, env_vars, template_service=self._template_service
            )
        except McpUnresolvedVariableError as exc:
            logger.warning(
                "mcp_proxy_unresolved_variable proxy=%s variable=%s header=%s",
                self.name,
                exc.variable_name,
                exc.header_name,
            )
            raise

    @contextlib.asynccontextmanager
    async def _connect_upstream(self, headers: dict[str, str] | None = None):
        headers_dict = dict(headers or {})
        sanitized_headers = sanitize_proxy_headers(
            headers_dict,
            env_vars=self._variable_supplier(),
            hidden_keys=self._hidden_keys_supplier(),
        )
        logger.debug(
            "mcp_proxy_connecting_upstream proxy=%s transport=%s "
            "header_keys=%s timeout=%.1f",
            self.name,
            self.upstream_transport,
            list(sanitized_headers.keys()),
            self.timeout,
        )
        if self.upstream_transport == "sse":
            async with sse_client(
                self.upstream_url,
                headers=headers_dict,
                timeout=self.timeout,
            ) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    yield session
        else:
            timeout = httpx.Timeout(self.timeout)
            async with create_mcp_http_client(headers=headers_dict, timeout=timeout) as http_client:
                async with streamable_http_client(
                    self.upstream_url,
                    http_client=http_client,
                ) as (read_stream, write_stream, _get_session_id):
                    async with ClientSession(read_stream, write_stream) as session:
                        await session.initialize()
                        yield session

    async def _dispatch_proxy_operation(
        self,
        operation: str,
        callback: Callable[[ClientSession], Awaitable[Any]],
        *,
        tool_name: str | None = None,
        mcp_arg_count: int | None = None,
    ) -> Any:
        """Run one upstream operation with common lifecycle and observability."""
        started = time.perf_counter()
        self._metrics.track_mcp_request_received("POST")
        logger.debug(
            "mcp_proxy_operation_started proxy=%s operation=%s",
            self.name,
            operation,
        )

        try:
            resolved_headers = self._resolve_headers()
            async with self._connect_upstream(resolved_headers) as session:
                result = await callback(session)
        except McpUnresolvedVariableError:
            duration_ms = (time.perf_counter() - started) * 1000.0
            self._record_proxy_failure(
                operation,
                "error",
                "Proxy variable could not be resolved",
                duration_ms,
                tool_name=tool_name,
                mcp_arg_count=mcp_arg_count,
            )
            raise
        except (httpx.TimeoutException, TimeoutError) as exc:
            duration_ms = (time.perf_counter() - started) * 1000.0
            self._record_proxy_failure(
                operation,
                "timeout",
                "Upstream request timed out",
                duration_ms,
                tool_name=tool_name,
                mcp_arg_count=mcp_arg_count,
            )
            raise TimeoutError(f"Upstream MCP server timed out: {exc}") from exc
        except (httpx.ConnectError, httpx.NetworkError) as exc:
            duration_ms = (time.perf_counter() - started) * 1000.0
            self._record_proxy_failure(
                operation,
                "connect_error",
                "Upstream connection failed",
                duration_ms,
                tool_name=tool_name,
                mcp_arg_count=mcp_arg_count,
            )
            raise httpx.ConnectError(
                f"Connection failed to upstream MCP server: {exc}"
            ) from exc
        except Exception:
            duration_ms = (time.perf_counter() - started) * 1000.0
            self._record_proxy_failure(
                operation,
                "error",
                "Upstream operation failed",
                duration_ms,
                tool_name=tool_name,
                mcp_arg_count=mcp_arg_count,
            )
            raise

        duration_ms = (time.perf_counter() - started) * 1000.0
        outcome = (
            "error"
            if operation == "call_tool" and getattr(result, "isError", False) is True
            else "success"
        )
        self._metrics.track_mcp_response_sent("POST", outcome)
        if operation == "call_tool":
            self._metrics.track_mcp_tool_call_duration(
                "POST", outcome, duration_ms / 1000.0
            )
        self._record_proxy_activity(
            operation,
            outcome,
            duration_ms,
            tool_name=tool_name,
            mcp_arg_count=mcp_arg_count,
            result=result,
        )
        self._log_proxy_success(
            operation,
            outcome,
            duration_ms,
            tool_name=tool_name,
            result=result,
        )
        return result

    def _record_proxy_failure(
        self,
        operation: str,
        log_suffix: str,
        detail: str,
        duration_ms: float,
        *,
        tool_name: str | None,
        mcp_arg_count: int | None,
    ) -> None:
        self._metrics.track_mcp_response_sent("POST", "error")
        if operation == "call_tool":
            self._metrics.track_mcp_tool_call_duration(
                "POST", "error", duration_ms / 1000.0
            )
        logger.error(
            "mcp_proxy_%s_%s proxy=%s%s duration_ms=%.2f",
            operation,
            log_suffix,
            self.name,
            f" tool={tool_name}" if tool_name is not None else "",
            duration_ms,
        )
        self._record_proxy_activity(
            operation,
            "error",
            duration_ms,
            tool_name=tool_name,
            mcp_arg_count=mcp_arg_count,
            detail=detail,
        )

    def _record_proxy_activity(
        self,
        operation: str,
        outcome: str,
        duration_ms: float,
        *,
        tool_name: str | None,
        mcp_arg_count: int | None,
        result: Any = None,
        detail: str | None = None,
    ) -> None:
        if self._activity_log is None:
            return
        if operation == "call_tool" and outcome == "success":
            sanitized_headers = sanitize_proxy_headers(
                self.headers,
                env_vars=self._variable_supplier(),
                hidden_keys=self._hidden_keys_supplier(),
            )
            if sanitized_headers:
                detail = f"Headers: {sanitized_headers}"
        tool_count = (
            len(result)
            if operation == "list_tools" and isinstance(result, (list, tuple))
            else None
        )
        self._activity_log.append(
            McpActivityEntry(
                id=str(uuid.uuid4()),
                timestamp=datetime.now(timezone.utc),
                operation=operation,
                outcome=outcome,
                tool_name=tool_name,
                tool_count=tool_count,
                mcp_arg_count=mcp_arg_count,
                detail=McpActivityEntry._sanitize_detail(detail),
                duration_ms=duration_ms,
            )
        )

    def _log_proxy_success(
        self,
        operation: str,
        outcome: str,
        duration_ms: float,
        *,
        tool_name: str | None,
        result: Any,
    ) -> None:
        if operation == "list_tools":
            logger.info(
                "mcp_proxy_list_tools_success proxy=%s tool_count=%d duration_ms=%.2f",
                self.name,
                len(result),
                duration_ms,
            )
        elif operation == "list_prompts":
            logger.info(
                "mcp_proxy_list_prompts_success proxy=%s prompt_count=%d duration_ms=%.2f",
                self.name,
                len(result),
                duration_ms,
            )
        elif operation == "list_resources":
            logger.info(
                "mcp_proxy_list_resources_success proxy=%s resource_count=%d duration_ms=%.2f",
                self.name,
                len(result),
                duration_ms,
            )
        elif operation == "call_tool":
            logger.info(
                "mcp_proxy_call_tool_completed proxy=%s tool=%s outcome=%s duration_ms=%.2f",
                self.name,
                tool_name,
                outcome,
                duration_ms,
            )
        elif operation == "get_prompt":
            logger.info(
                "mcp_proxy_get_prompt_completed proxy=%s prompt=%s duration_ms=%.2f",
                self.name,
                tool_name,
                duration_ms,
            )
        else:
            logger.info(
                "mcp_proxy_read_resource_completed proxy=%s uri=%s duration_ms=%.2f",
                self.name,
                tool_name,
                duration_ms,
            )

    async def list_tools(self) -> list[Any]:
        async def invoke(session: ClientSession) -> list[Any]:
            result = await session.list_tools()
            tools = getattr(result, "tools", result)
            return list(tools) if isinstance(tools, (list, tuple)) else list(tools or [])

        return cast(list[Any], await self._dispatch_proxy_operation("list_tools", invoke))

    async def call_tool(self, name: str, arguments: dict | None = None) -> Any:
        mcp_args = dict(arguments or {})
        return await self._dispatch_proxy_operation(
            "call_tool",
            lambda session: session.call_tool(name, mcp_args),
            tool_name=name,
            mcp_arg_count=len(mcp_args),
        )

    async def list_prompts(self) -> list[Any]:
        async def invoke(session: ClientSession) -> list[Any]:
            result = await session.list_prompts()
            prompts = getattr(result, "prompts", result)
            return list(prompts) if isinstance(prompts, (list, tuple)) else list(prompts or [])

        return cast(list[Any], await self._dispatch_proxy_operation("list_prompts", invoke))

    async def get_prompt(self, name: str, arguments: dict | None = None) -> Any:
        return await self._dispatch_proxy_operation(
            "get_prompt",
            lambda session: session.get_prompt(name, arguments or {}),
            tool_name=name,
        )

    async def list_resources(self) -> list[Any]:
        async def invoke(session: ClientSession) -> list[Any]:
            result = await session.list_resources()
            resources = getattr(result, "resources", result)
            return (
                list(resources)
                if isinstance(resources, (list, tuple))
                else list(resources or [])
            )

        return cast(list[Any], await self._dispatch_proxy_operation("list_resources", invoke))

    async def read_resource(self, uri: Any) -> Any:
        return await self._dispatch_proxy_operation(
            "read_resource",
            lambda session: session.read_resource(uri),
            tool_name=str(uri),
        )

    def create_app(self) -> Starlette:
        mcp_route, lifespan = build_streamable_http_route(self.server)
        return Starlette(
            debug=False,
            routes=[
                mcp_route,
                Mount(MCP_LEGACY_SSE_MOUNT_PATH, app=self._create_sse_app()),
            ],
            lifespan=lifespan,
        )

    def _create_sse_app(self) -> Starlette:
        """Legacy HTTP+SSE transport for backward-compatible clients."""
        return build_legacy_sse_app(self.server, debug=False)
