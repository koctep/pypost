from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import Callable, Sequence
from typing import Any, Dict, List

from starlette.applications import Starlette
from mcp.server import Server
from mcp.types import TextContent, Tool
from starlette.concurrency import run_in_threadpool
from starlette.routing import Mount

from pypost.core.environment_variable_resolver import resolve_environment_variables
from pypost.core.mcp_activity_log import McpActivityEntry, McpActivityLog
from pypost.core.mcp_response_sanitizer import McpResponseSanitizer
from pypost.core.mcp_secrets_policy import McpSecretsPolicy
from pypost.core.mcp_tool_contract import (
    McpArgumentValidationError,
    build_tool_input_schema,
    normalize_mcp_tool_name,
    resolve_mcp_call_param_specs,
    tool_description,
    validate_mcp_execution_arguments,
)
from pypost.core.mcp_legacy_sse import build_legacy_sse_app
from pypost.core.mcp_observability import (
    record_mcp_call_outcome,
    record_mcp_validation_failure,
    validate_mcp_call_arguments,
)
from pypost.core.mcp_streamable_http import build_streamable_http_route
from pypost.core.mcp_transport_routes import MCP_LEGACY_SSE_MOUNT_PATH
from pypost.core.metrics_protocol import MetricsTrackerProtocol, resolve_metrics
from pypost.core.execute_request_protocol import ExecuteRequestProtocol
from pypost.core.request_service import ExecutionResult, RequestService
from pypost.core.template_service import TemplateService
from pypost.core.websocket_mcp_tools import (
    build_websocket_mcp_tool_schema,
    execute_websocket_probe,
    resolve_websocket_mcp_call_specs,
)
from pypost.models.models import RequestData
from pypost.models.settings import AppSettings
from pypost.models.websocket import WebSocketConnection


logger = logging.getLogger(__name__)

DEFAULT_MAX_CONCURRENT_MCP_CALLS = 4


def _merge_execution_variables(
    env_vars: dict[str, str], mcp_args: dict[str, Any]
) -> dict[str, Any]:
    """Merge one endpoint's environment snapshot with mcp.request namespace."""
    return {**env_vars, "mcp": {"request": mcp_args}}


def _tool_result_has_error(result: ExecutionResult) -> bool:
    """True when PyPost failed to execute the request (not upstream HTTP 4xx/5xx)."""
    if result.execution_error is not None:
        return True
    return result.response.status_code == 0


def format_structured_tool_result(
    result: ExecutionResult,
    *,
    env_vars: dict[str, str] | None = None,
    hidden_keys: set[str] | None = None,
) -> str:
    """Serialize ExecutionResult as agent-facing JSON (status, error, body, optional logs)."""
    env, hidden = env_vars or {}, hidden_keys or set()
    body = McpResponseSanitizer.sanitize_body(
        result.response.body, env_vars=env, hidden_keys=hidden
    )
    payload: dict[str, Any] = {
        "status": result.response.status_code,
        "error": _tool_result_has_error(result),
        "body": body,
    }
    if result.script_logs:
        payload["logs"] = McpResponseSanitizer.sanitize_logs(
            result.script_logs, env_vars=env, hidden_keys=hidden
        )
    if result.execution_error is not None:
        payload["error_category"] = result.execution_error.category.value
        payload["error_message"] = result.execution_error.message
        if result.execution_error.detail is not None:
            payload["error_detail"] = McpResponseSanitizer.sanitize_text(
                result.execution_error.detail, env_vars=env, hidden_keys=hidden
            )
    return json.dumps(payload, ensure_ascii=False)


class MCPServerImpl:
    def __init__(
        self,
        name: str = "pypost-server",
        metrics: MetricsTrackerProtocol | None = None,
        template_service: TemplateService | None = None,
        variable_supplier: Callable[[], dict[str, str]] | None = None,
        hidden_keys_supplier: Callable[[], set[str]] | None = None,
        activity_log: McpActivityLog | None = None,
        settings: AppSettings | None = None,
    ):
        self.server = Server(name)
        self.tools_map: Dict[str, RequestData | WebSocketConnection] = {}
        self._metrics = resolve_metrics(metrics)
        self._activity_log = activity_log
        self._template_service = template_service
        self._settings = settings
        self._variable_supplier = variable_supplier or (lambda: {})
        self._hidden_keys_supplier = hidden_keys_supplier or (lambda: set())
        self._call_tool_semaphore = asyncio.Semaphore(DEFAULT_MAX_CONCURRENT_MCP_CALLS)
        if template_service is not None:
            logger.debug(
                "MCPServerImpl: using injected TemplateService id=%d", id(template_service)
            )

        # Register handlers
        self.server.list_tools()(self.list_tools)
        self.server.call_tool(validate_input=False)(self.call_tool)

    async def list_tools(self) -> List[Tool]:
        tools = []
        for name, item in self.tools_map.items():
            if isinstance(item, WebSocketConnection):
                schema = build_websocket_mcp_tool_schema(
                    item, self._template_service, self._hidden_keys_supplier()
                )
                desc = item.mcp_description or f"Sample real-time stream from {item.name}"
            else:
                schema, desc = self._generate_schema(item), tool_description(item)
            tools.append(Tool(name=name, description=desc, inputSchema=schema))
        if self._activity_log is not None:
            self._activity_log.append(McpActivityEntry.new_list_tools(len(tools)))
        return tools

    async def call_tool(self, name: str, arguments: dict) -> List[Any]:
        async with self._call_tool_semaphore:
            return await self._call_tool_inner(name, arguments)

    async def _call_tool_inner(self, name: str, arguments: dict) -> List[Any]:
        if name not in self.tools_map:
            raise ValueError(f"Tool {name} not found")

        item = self.tools_map[name]
        arguments = arguments or {}
        mcp_arg_count = len(arguments)
        started = time.perf_counter()
        if isinstance(item, WebSocketConnection):
            transport, method = "websocket", "WEBSOCKET"
            complete_specs, visible_specs = resolve_websocket_mcp_call_specs(
                item, self._hidden_keys_supplier()
            )
        else:
            transport, method = "http", item.method
            complete_specs, visible_specs = resolve_mcp_call_param_specs(
                item,  # type: ignore[arg-type]
                self._template_service,
                self._hidden_keys_supplier(),
            )
        validate_mcp_call_arguments(
            arguments, visible_specs, complete_specs, "preflight", transport, name,
            method, mcp_arg_count, started, self._metrics, self._activity_log
        )
        if isinstance(item, WebSocketConnection):
            return await run_in_threadpool(
                execute_websocket_probe,
                item,
                arguments,
                env_vars=self._variable_supplier(),
                hidden_keys=self._hidden_keys_supplier(),
                settings=self._settings,
                template_service=self._template_service,
                metrics=self._metrics,
                activity_log=self._activity_log,
            )
        self._metrics.track_mcp_request_received(method)
        try:
            env_vars = self._variable_supplier()
            hidden_keys = self._hidden_keys_supplier()
            result = await run_in_threadpool(
                self._execute_request_sync,
                item,
                arguments,
                env_vars,
                hidden_keys,
            )
            output_text = format_structured_tool_result(
                result, env_vars=env_vars, hidden_keys=hidden_keys
            )
            has_error = _tool_result_has_error(result)
            outcome = "error" if has_error else "success"
            detail = result.execution_error.message if result.execution_error else None
            http_status = result.response.status_code
        except McpArgumentValidationError as error:
            record_mcp_validation_failure(
                error, "execution_boundary", transport, name, method, mcp_arg_count,
                (time.perf_counter() - started) * 1000.0, self._metrics,
                self._activity_log
            )
            raise
        except Exception as e:
            output_text = f"Error executing request: {str(e)}"
            outcome = "error"
            detail = str(e)
            http_status = None
        duration_ms = (time.perf_counter() - started) * 1000.0
        record_mcp_call_outcome(
            self._metrics, self._activity_log, method, outcome, name,
            mcp_arg_count, http_status, detail, duration_ms
        )
        return [TextContent(type="text", text=output_text)]

    def set_variable_supplier(
        self, supplier: Callable[[], dict[str, str]] | None
    ) -> None:
        self._variable_supplier = supplier or (lambda: {})

    def set_hidden_keys_supplier(
        self, supplier: Callable[[], set[str]] | None
    ) -> None:
        self._hidden_keys_supplier = supplier or (lambda: set())

    def _build_execution_variables(
        self,
        mcp_args: dict[str, Any],
        env_vars: dict[str, str],
        hidden_keys: set[str],
        request_data: RequestData | None = None,
    ) -> dict[str, Any]:
        merged_args, defaults_applied = dict(mcp_args or {}), 0
        if request_data is not None and request_data.mcp_params:
            for param_name, param_spec in request_data.mcp_params.items():
                if (
                    param_name not in merged_args
                    or merged_args[param_name] is None
                ) and param_spec.default is not None:
                    merged_args[param_name] = param_spec.default
                    defaults_applied += 1
                    self._metrics.track_mcp_param_default_applied(request_data.method)
                    logger.info(
                        "mcp_param_default_applied method=%s param=%s "
                        "default_applied=true default_type=%s",
                        request_data.method,
                        param_name,
                        param_spec.type,
                    )
        if request_data is not None:
            validate_mcp_execution_arguments(request_data, merged_args)
        counts = McpSecretsPolicy.safe_execution_log_fields(
            len(env_vars), len(hidden_keys), len(merged_args)
        )
        logger.debug(
            "mcp_execution_variables_merged env_var_count=%d "
            "hidden_key_count=%d mcp_arg_count=%d defaults_applied_count=%d",
            counts["env_var_count"],
            counts["hidden_key_count"],
            counts["mcp_arg_count"],
            defaults_applied,
        )
        resolved_env_vars = resolve_environment_variables(
            env_vars,
            template_service=self._template_service,
            render_path="mcp",
        )
        execution_env = McpSecretsPolicy.execution_environment_variables(resolved_env_vars)
        return _merge_execution_variables(execution_env, merged_args)

    def _create_request_service(self) -> ExecuteRequestProtocol:
        """Return an isolated RequestService for one MCP tool invocation (PYPOST-138)."""
        logger.debug("MCPServerImpl: creating RequestService for MCP call")
        return RequestService(
            metrics=self._metrics,
            template_service=self._template_service,
        )

    def _execute_request_sync(
        self,
        request_data: RequestData,
        args: dict,
        env_vars: dict[str, str],
        hidden_keys: set[str],
    ):
        variables = self._build_execution_variables(
            args, env_vars, hidden_keys, request_data=request_data
        )
        return self._create_request_service().execute(
            request_data, variables, hidden_keys=hidden_keys
        )

    def register_tools(self, requests: Sequence[RequestData | WebSocketConnection]):
        """Register HTTP requests and WebSocket connections as MCP tools."""
        self.tools_map.clear()
        for item in requests:
            if item.expose_as_mcp:
                pfx = "ws_" if isinstance(item, WebSocketConnection) else ""
                self.tools_map[f"{pfx}{normalize_mcp_tool_name(item.name)}"] = item

    def _generate_schema(self, req: RequestData) -> dict:
        hidden_keys = self._hidden_keys_supplier()
        _, visible_specs = resolve_mcp_call_param_specs(
            req, self._template_service, hidden_keys
        )
        return build_tool_input_schema(visible_specs)

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
