"""Transparent MCP Reverse Proxy implementation.

Forwards standard MCP protocol operations (tools, prompts, resources) to
an external upstream MCP server with dynamic environment variable header resolution.
"""
from __future__ import annotations

import contextlib
import logging
import time
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any, Literal

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
            "mcp_proxy_connecting_upstream proxy=%s transport=%s url=%s "
            "header_keys=%s timeout=%.1f",
            self.name,
            self.upstream_transport,
            self.upstream_url,
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

    async def list_tools(self) -> list[Any]:
        started = time.perf_counter()
        logger.debug("mcp_proxy_list_tools_started proxy=%s", self.name)
        try:
            resolved_headers = self._resolve_headers()
        except McpUnresolvedVariableError as exc:
            duration_ms = (time.perf_counter() - started) * 1000.0
            if self._activity_log is not None:
                self._activity_log.append(
                    McpActivityEntry(
                        id=str(uuid.uuid4()),
                        timestamp=datetime.now(timezone.utc),
                        operation="list_tools",
                        outcome="error",
                        detail=str(exc),
                        duration_ms=duration_ms,
                    )
                )
            raise

        try:
            async with self._connect_upstream(resolved_headers) as session:
                result = await session.list_tools()
                tools = getattr(result, "tools", result)
                tools_list: list[Any] = (
                    list(tools) if isinstance(tools, (list, tuple)) else list(tools or [])
                )
                duration_ms = (time.perf_counter() - started) * 1000.0
                logger.info(
                    "mcp_proxy_list_tools_success proxy=%s tool_count=%d duration_ms=%.2f",
                    self.name,
                    len(tools_list),
                    duration_ms,
                )
                if self._activity_log is not None:
                    self._activity_log.append(
                        McpActivityEntry.new_list_tools(len(tools_list))
                    )
                return tools_list
        except (httpx.TimeoutException, TimeoutError) as exc:
            duration_ms = (time.perf_counter() - started) * 1000.0
            logger.error(
                "mcp_proxy_list_tools_timeout proxy=%s url=%s error=%s duration_ms=%.2f",
                self.name,
                self.upstream_url,
                exc,
                duration_ms,
            )
            if self._activity_log is not None:
                self._activity_log.append(
                    McpActivityEntry(
                        id=str(uuid.uuid4()),
                        timestamp=datetime.now(timezone.utc),
                        operation="list_tools",
                        outcome="error",
                        detail=f"Upstream timed out: {exc}",
                        duration_ms=duration_ms,
                    )
                )
            raise TimeoutError(f"Upstream MCP server timed out: {exc}") from exc
        except (httpx.ConnectError, httpx.NetworkError) as exc:
            duration_ms = (time.perf_counter() - started) * 1000.0
            logger.error(
                "mcp_proxy_list_tools_connect_error proxy=%s url=%s error=%s duration_ms=%.2f",
                self.name,
                self.upstream_url,
                exc,
                duration_ms,
            )
            if self._activity_log is not None:
                self._activity_log.append(
                    McpActivityEntry(
                        id=str(uuid.uuid4()),
                        timestamp=datetime.now(timezone.utc),
                        operation="list_tools",
                        outcome="error",
                        detail=f"Connection failed: {exc}",
                        duration_ms=duration_ms,
                    )
                )
            raise httpx.ConnectError(f"Connection failed to upstream MCP server: {exc}") from exc
        except Exception as exc:
            duration_ms = (time.perf_counter() - started) * 1000.0
            logger.error(
                "mcp_proxy_list_tools_error proxy=%s error=%s duration_ms=%.2f",
                self.name,
                exc,
                duration_ms,
            )
            if self._activity_log is not None:
                self._activity_log.append(
                    McpActivityEntry(
                        id=str(uuid.uuid4()),
                        timestamp=datetime.now(timezone.utc),
                        operation="list_tools",
                        outcome="error",
                        detail=str(exc),
                        duration_ms=duration_ms,
                    )
                )
            raise

    async def call_tool(self, name: str, arguments: dict | None = None) -> Any:
        mcp_args = dict(arguments or {})
        started = time.perf_counter()
        self._metrics.track_mcp_request_received("POST")
        try:
            resolved_headers = self._resolve_headers()
        except McpUnresolvedVariableError as exc:
            duration_ms = (time.perf_counter() - started) * 1000.0
            self._metrics.track_mcp_response_sent("POST", "error")
            self._metrics.track_mcp_tool_call_duration("POST", "error", duration_ms / 1000.0)
            if self._activity_log is not None:
                self._activity_log.append(
                    McpActivityEntry.new_call_tool(
                        name,
                        outcome="error",
                        mcp_arg_count=len(mcp_args),
                        detail=str(exc),
                        duration_ms=duration_ms,
                    )
                )
            raise

        try:
            async with self._connect_upstream(resolved_headers) as session:
                result = await session.call_tool(name, mcp_args)
                duration_ms = (time.perf_counter() - started) * 1000.0
                is_error = getattr(result, "isError", False)
                outcome = "error" if is_error else "success"

                self._metrics.track_mcp_response_sent("POST", outcome)
                self._metrics.track_mcp_tool_call_duration("POST", outcome, duration_ms / 1000.0)

                logger.info(
                    "mcp_proxy_call_tool_completed proxy=%s tool=%s outcome=%s duration_ms=%.2f",
                    self.name,
                    name,
                    outcome,
                    duration_ms,
                )

                if self._activity_log is not None:
                    sanitized_headers = sanitize_proxy_headers(
                        self.headers,
                        env_vars=self._variable_supplier(),
                        hidden_keys=self._hidden_keys_supplier(),
                    )
                    self._activity_log.append(
                        McpActivityEntry.new_call_tool(
                            name,
                            outcome=outcome,
                            mcp_arg_count=len(mcp_args),
                            detail=f"Headers: {sanitized_headers}" if sanitized_headers else None,
                            duration_ms=duration_ms,
                        )
                    )
                return result
        except (httpx.TimeoutException, TimeoutError) as exc:
            duration_ms = (time.perf_counter() - started) * 1000.0
            self._metrics.track_mcp_response_sent("POST", "error")
            self._metrics.track_mcp_tool_call_duration("POST", "error", duration_ms / 1000.0)
            logger.error(
                "mcp_proxy_call_tool_timeout proxy=%s tool=%s url=%s error=%s duration_ms=%.2f",
                self.name,
                name,
                self.upstream_url,
                exc,
                duration_ms,
            )
            if self._activity_log is not None:
                self._activity_log.append(
                    McpActivityEntry.new_call_tool(
                        name,
                        outcome="error",
                        mcp_arg_count=len(mcp_args),
                        detail=f"Upstream timed out: {exc}",
                        duration_ms=duration_ms,
                    )
                )
            raise TimeoutError(f"Upstream MCP server timed out: {exc}") from exc
        except (httpx.ConnectError, httpx.NetworkError) as exc:
            duration_ms = (time.perf_counter() - started) * 1000.0
            self._metrics.track_mcp_response_sent("POST", "error")
            self._metrics.track_mcp_tool_call_duration("POST", "error", duration_ms / 1000.0)
            logger.error(
                "mcp_proxy_call_tool_connect_error proxy=%s tool=%s url=%s error=%s "
                "duration_ms=%.2f",
                self.name,
                name,
                self.upstream_url,
                exc,
                duration_ms,
            )
            if self._activity_log is not None:
                self._activity_log.append(
                    McpActivityEntry.new_call_tool(
                        name,
                        outcome="error",
                        mcp_arg_count=len(mcp_args),
                        detail=f"Connection failed: {exc}",
                        duration_ms=duration_ms,
                    )
                )
            raise httpx.ConnectError(f"Connection failed to upstream MCP server: {exc}") from exc
        except Exception as exc:
            duration_ms = (time.perf_counter() - started) * 1000.0
            self._metrics.track_mcp_response_sent("POST", "error")
            self._metrics.track_mcp_tool_call_duration("POST", "error", duration_ms / 1000.0)
            logger.error(
                "mcp_proxy_call_tool_error proxy=%s tool=%s error=%s duration_ms=%.2f",
                self.name,
                name,
                exc,
                duration_ms,
            )
            if self._activity_log is not None:
                self._activity_log.append(
                    McpActivityEntry.new_call_tool(
                        name,
                        outcome="error",
                        mcp_arg_count=len(mcp_args),
                        detail=str(exc),
                        duration_ms=duration_ms,
                    )
                )
            raise

    async def list_prompts(self) -> list[Any]:
        started = time.perf_counter()
        logger.debug("mcp_proxy_list_prompts_started proxy=%s", self.name)
        resolved_headers = self._resolve_headers()
        async with self._connect_upstream(resolved_headers) as session:
            result = await session.list_prompts()
            prompts = getattr(result, "prompts", result)
            prompts_list = (
                list(prompts) if isinstance(prompts, (list, tuple)) else list(prompts or [])
            )
            duration_ms = (time.perf_counter() - started) * 1000.0
            logger.info(
                "mcp_proxy_list_prompts_success proxy=%s prompt_count=%d duration_ms=%.2f",
                self.name,
                len(prompts_list),
                duration_ms,
            )
            return prompts_list

    async def get_prompt(self, name: str, arguments: dict | None = None) -> Any:
        started = time.perf_counter()
        logger.debug("mcp_proxy_get_prompt_started proxy=%s prompt=%s", self.name, name)
        resolved_headers = self._resolve_headers()
        async with self._connect_upstream(resolved_headers) as session:
            res = await session.get_prompt(name, arguments or {})
            duration_ms = (time.perf_counter() - started) * 1000.0
            logger.info(
                "mcp_proxy_get_prompt_completed proxy=%s prompt=%s duration_ms=%.2f",
                self.name,
                name,
                duration_ms,
            )
            return res

    async def list_resources(self) -> list[Any]:
        started = time.perf_counter()
        logger.debug("mcp_proxy_list_resources_started proxy=%s", self.name)
        resolved_headers = self._resolve_headers()
        async with self._connect_upstream(resolved_headers) as session:
            result = await session.list_resources()
            resources = getattr(result, "resources", result)
            resources_list = (
                list(resources)
                if isinstance(resources, (list, tuple))
                else list(resources or [])
            )
            duration_ms = (time.perf_counter() - started) * 1000.0
            logger.info(
                "mcp_proxy_list_resources_success proxy=%s resource_count=%d duration_ms=%.2f",
                self.name,
                len(resources_list),
                duration_ms,
            )
            return resources_list

    async def read_resource(self, uri: Any) -> Any:
        started = time.perf_counter()
        logger.debug("mcp_proxy_read_resource_started proxy=%s uri=%s", self.name, uri)
        resolved_headers = self._resolve_headers()
        async with self._connect_upstream(resolved_headers) as session:
            res = await session.read_resource(uri)
            duration_ms = (time.perf_counter() - started) * 1000.0
            logger.info(
                "mcp_proxy_read_resource_completed proxy=%s uri=%s duration_ms=%.2f",
                self.name,
                uri,
                duration_ms,
            )
            return res

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
