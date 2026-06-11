import json
import logging
import time
from collections.abc import Callable
from typing import Any, Dict, List

from starlette.applications import Starlette

from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import TextContent, Tool
from starlette.concurrency import run_in_threadpool
from starlette.responses import Response
from starlette.routing import Mount, Route

from pypost.core.mcp_activity_log import McpActivityEntry, McpActivityLog
from pypost.core.mcp_secrets_policy import McpSecretsPolicy
from pypost.core.mcp_tool_contract import (
    build_tool_input_schema,
    normalize_mcp_tool_name,
    resolve_mcp_param_specs,
    tool_description,
)
from pypost.core.mcp_streamable_http import build_streamable_http_route
from pypost.core.mcp_transport_routes import (
    MCP_LEGACY_SSE_MESSAGES_PATH,
    MCP_LEGACY_SSE_MOUNT_PATH,
)
from pypost.core.metrics import MetricsManager
from pypost.core.request_service import ExecutionResult, RequestService
from pypost.core.template_service import TemplateService
from pypost.models.models import RequestData

logger = logging.getLogger(__name__)


def _merge_execution_variables(
    env_vars: dict[str, str], mcp_args: dict[str, Any]
) -> dict[str, Any]:
    """Merge active env snapshot with mcp.request namespace."""
    return {**env_vars, "mcp": {"request": mcp_args}}


def _tool_result_has_error(result: ExecutionResult) -> bool:
    """True when PyPost failed to execute the request (not upstream HTTP 4xx/5xx)."""
    if result.execution_error is not None:
        return True
    return result.response.status_code == 0


def format_structured_tool_result(result: ExecutionResult) -> str:
    """Serialize ExecutionResult as agent-facing JSON (status, error, body, optional logs)."""
    payload: dict[str, Any] = {
        "status": result.response.status_code,
        "error": _tool_result_has_error(result),
        "body": result.response.body,
    }
    if result.script_logs:
        payload["logs"] = result.script_logs
    if result.execution_error is not None:
        payload["error_category"] = result.execution_error.category.value
        payload["error_message"] = result.execution_error.message
    return json.dumps(payload, ensure_ascii=False)


class MCPServerImpl:
    def __init__(
        self,
        name: str = "pypost-server",
        metrics: MetricsManager | None = None,
        template_service: TemplateService | None = None,
        variable_supplier: Callable[[], dict[str, str]] | None = None,
        hidden_keys_supplier: Callable[[], set[str]] | None = None,
        activity_log: McpActivityLog | None = None,
    ):
        self.server = Server(name)
        self.tools_map: Dict[str, RequestData] = {}
        self._metrics = metrics
        self._activity_log = activity_log
        self._template_service = template_service
        self._variable_supplier = variable_supplier or (lambda: {})
        self._hidden_keys_supplier = hidden_keys_supplier or (lambda: set())
        if template_service is not None:
            logger.debug(
                "MCPServerImpl: using injected TemplateService id=%d", id(template_service)
            )
        self.request_service = RequestService(
            metrics=self._metrics, template_service=self._template_service
        )

        # Register handlers
        self.server.list_tools()(self.list_tools)
        self.server.call_tool()(self.call_tool)

    async def list_tools(self) -> List[Tool]:
        tools = []
        for name, req in self.tools_map.items():
            schema = self._generate_schema(req)
            tools.append(
                Tool(
                    name=name,
                    description=tool_description(req),
                    inputSchema=schema,
                )
            )
        if self._activity_log is not None:
            self._activity_log.append(McpActivityEntry.new_list_tools(len(tools)))
        return tools

    async def call_tool(self, name: str, arguments: dict) -> List[Any]:
        if name not in self.tools_map:
            raise ValueError(f"Tool {name} not found")

        request_data = self.tools_map[name]
        mcp_arg_count = len(arguments or {})
        started = time.perf_counter()

        # Track MCP request
        if self._metrics:
            self._metrics.track_mcp_request_received(request_data.method)

        # Execute request in threadpool since RequestService is synchronous
        try:
            result = await run_in_threadpool(
                self._execute_request_sync, request_data, arguments
            )
            output_text = format_structured_tool_result(result)
            duration_ms = (time.perf_counter() - started) * 1000.0
            has_error = _tool_result_has_error(result)
            outcome = "error" if has_error else "success"

            if self._metrics:
                self._metrics.track_mcp_response_sent(request_data.method, outcome)

            if self._activity_log is not None:
                detail = None
                if result.execution_error is not None:
                    detail = result.execution_error.message
                self._activity_log.append(
                    McpActivityEntry.new_call_tool(
                        name,
                        outcome=outcome,
                        mcp_arg_count=mcp_arg_count,
                        http_status=result.response.status_code,
                        detail=detail,
                        duration_ms=duration_ms,
                    )
                )

            return [TextContent(type="text", text=output_text)]
        except Exception as e:
            duration_ms = (time.perf_counter() - started) * 1000.0
            # Track MCP response error
            if self._metrics:
                self._metrics.track_mcp_response_sent(request_data.method, "error")
            if self._activity_log is not None:
                self._activity_log.append(
                    McpActivityEntry.new_call_tool(
                        name,
                        outcome="error",
                        mcp_arg_count=mcp_arg_count,
                        detail=str(e),
                        duration_ms=duration_ms,
                    )
                )
            return [TextContent(type="text", text=f"Error executing request: {str(e)}")]

    def set_variable_supplier(
        self, supplier: Callable[[], dict[str, str]] | None
    ) -> None:
        self._variable_supplier = supplier or (lambda: {})

    def set_hidden_keys_supplier(
        self, supplier: Callable[[], set[str]] | None
    ) -> None:
        self._hidden_keys_supplier = supplier or (lambda: set())

    def _build_execution_variables(self, mcp_args: dict[str, Any]) -> dict[str, Any]:
        env_vars = self._variable_supplier()
        hidden_keys = self._hidden_keys_supplier()
        counts = McpSecretsPolicy.safe_execution_log_fields(
            len(env_vars),
            len(hidden_keys),
            len(mcp_args),
        )
        logger.debug(
            "mcp_execution_variables_merged env_var_count=%d "
            "hidden_key_count=%d mcp_arg_count=%d",
            counts["env_var_count"],
            counts["hidden_key_count"],
            counts["mcp_arg_count"],
        )
        execution_env = McpSecretsPolicy.execution_environment_variables(env_vars)
        return _merge_execution_variables(execution_env, mcp_args)

    def _execute_request_sync(self, request_data: RequestData, args: dict):
        variables = self._build_execution_variables(args)
        return self.request_service.execute(request_data, variables)

    def register_tools(self, requests: List[RequestData]):
        self.tools_map.clear()
        for req in requests:
            if req.expose_as_mcp:
                tool_name = normalize_mcp_tool_name(req.name)
                self.tools_map[tool_name] = req

    def _generate_schema(self, req: RequestData) -> dict:
        hidden_keys = self._hidden_keys_supplier()
        discovered = McpSecretsPolicy.extract_mcp_request_variables(req)
        specs = resolve_mcp_param_specs(req, discovered)
        specs = McpSecretsPolicy.filter_agent_param_specs(
            specs, req, self._template_service, hidden_keys
        )
        return build_tool_input_schema(specs)

    def create_app(self) -> Starlette:
        mcp_route, lifespan = build_streamable_http_route(self.server)
        return Starlette(
            debug=True,
            routes=[
                mcp_route,
                Mount(MCP_LEGACY_SSE_MOUNT_PATH, app=self._create_sse_app()),
            ],
            lifespan=lifespan,
        )

    def _create_sse_app(self) -> Starlette:
        """Legacy HTTP+SSE transport for backward-compatible clients."""
        sse = SseServerTransport(MCP_LEGACY_SSE_MESSAGES_PATH)

        class SSEEndpoint:
            def __init__(self, server, sse_transport):
                self.server = server
                self.sse_transport = sse_transport

            async def __call__(self, scope, receive, send):
                if scope.get("method") != "GET":
                    await send(
                        {
                            "type": "http.response.start",
                            "status": 405,
                            "headers": [(b"content-type", b"text/plain")],
                        }
                    )
                    await send(
                        {
                            "type": "http.response.body",
                            "body": b"Method Not Allowed",
                        }
                    )
                    return
                async with self.sse_transport.connect_sse(scope, receive, send) as streams:
                    opts = self.server.create_initialization_options()
                    await self.server.run(streams[0], streams[1], opts)

        class MessagesEndpoint:
            def __init__(self, sse_transport):
                self.sse_transport = sse_transport

            async def __call__(self, scope, receive, send):
                if scope["type"] == "http" and scope["method"] != "POST":
                    await self._send_response(send, 405, b"Method Not Allowed")
                    return
                await self.sse_transport.handle_post_message(scope, receive, send)

            async def _send_response(self, send, status, body):
                await send(
                    {
                        "type": "http.response.start",
                        "status": status,
                        "headers": [
                            (b"content-type", b"text/plain"),
                        ],
                    }
                )
                await send(
                    {
                        "type": "http.response.body",
                        "body": body,
                    }
                )

        async def handle_sse_get(request):
            ep = SSEEndpoint(self.server, sse)
            await ep(request.scope, request.receive, request._send)
            return Response()

        return Starlette(
            debug=True,
            routes=[
                Mount(MCP_LEGACY_SSE_MESSAGES_PATH, app=MessagesEndpoint(sse)),
                Route("/", endpoint=handle_sse_get, methods=["GET"]),
            ],
        )
