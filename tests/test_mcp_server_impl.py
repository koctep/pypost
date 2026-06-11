"""Tests for MCPServerImpl: tool registration, schemas, routing, and call_tool path."""
import pytest

pytestmark = pytest.mark.timeout(60)

import asyncio
import json
import unittest
from unittest.mock import MagicMock

from mcp.types import TextContent
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.testclient import TestClient

from pypost.core.mcp_server_impl import (
    MCPServerImpl,
    _merge_execution_variables,
    _tool_result_has_error,
    format_structured_tool_result,
)
from pypost.core.mcp_transport_routes import (
    MCP_LEGACY_SSE_MESSAGES_PATH,
    MCP_LEGACY_SSE_MOUNT_PATH,
    MCP_STREAMABLE_HTTP_PATH,
)
from pypost.core.mcp_tool_contract import (
    build_tool_input_schema,
    resolve_mcp_param_specs,
    tool_description,
)
from pypost.core.request_service import ExecutionResult
from pypost.models.errors import ErrorCategory, ExecutionError
from pypost.models.models import McpToolParam, RequestData
from pypost.models.response import ResponseData


def _exec_result(body="ok", logs=None, script_error=None, status_code=200):
    execution_error = None
    if script_error:
        execution_error = ExecutionError(
            category=ErrorCategory.SCRIPT,
            message="Post-script execution failed.",
            detail=script_error,
        )
    return ExecutionResult(
        response=ResponseData(
            status_code=status_code,
            headers={},
            body=body,
            elapsed_time=0.01,
            size=len(body.encode("utf-8")),
        ),
        updated_variables={},
        script_logs=logs or [],
        execution_error=execution_error,
    )


def _parse_tool_result(text: str) -> dict:
    return json.loads(text)


class TestMCPServerImpl(unittest.TestCase):
    def test_register_tools_keeps_only_exposed_and_normalizes_names(self):
        impl = MCPServerImpl()
        exposed = RequestData(
            name="Fetch User", expose_as_mcp=True, method="GET", url="http://x"
        )
        hidden = RequestData(name="Hidden", expose_as_mcp=False, method="GET", url="http://y")
        impl.register_tools([exposed, hidden])
        self.assertEqual(list(impl.tools_map.keys()), ["fetch_user"])
        self.assertIs(impl.tools_map["fetch_user"], exposed)

    def test_register_tools_clears_previous_map(self):
        impl = MCPServerImpl()
        first = RequestData(name="A", expose_as_mcp=True, method="GET", url="http://a")
        second = RequestData(name="B", expose_as_mcp=True, method="GET", url="http://b")
        impl.register_tools([first])
        impl.register_tools([second])
        self.assertEqual(list(impl.tools_map.keys()), ["b"])

    def test_register_tools_sets_mcp_server_up_metric(self):
        metrics = MagicMock()
        impl = MCPServerImpl(metrics=metrics)
        req = RequestData(name="Tool", expose_as_mcp=True, method="GET", url="http://u")
        impl.register_tools([req])
        metrics.set_mcp_server_up.assert_called_once_with(True)
        impl.register_tools([])
        metrics.set_mcp_server_up.assert_called_with(False)

    def test_list_tools_uses_mcp_description_when_set(self):
        impl = MCPServerImpl()
        req = RequestData(
            name="Echo",
            mcp_description="Returns an echo response",
            expose_as_mcp=True,
            method="GET",
            url="http://example.com",
        )
        impl.register_tools([req])
        tools = asyncio.run(impl.list_tools())
        self.assertEqual(tools[0].description, "Returns an echo response")

    def test_list_tools_falls_back_to_request_name_for_description(self):
        impl = MCPServerImpl()
        req = RequestData(
            name="Echo Tool",
            expose_as_mcp=True,
            method="GET",
            url="http://example.com",
        )
        impl.register_tools([req])
        tools = asyncio.run(impl.list_tools())
        self.assertEqual(tools[0].description, "Echo Tool")

    def test_list_tools_schema_uses_param_metadata(self):
        impl = MCPServerImpl()
        req = RequestData(
            name="Echo",
            expose_as_mcp=True,
            method="GET",
            url="http://{{ mcp.request.host }}/p",
            mcp_params={
                "host": McpToolParam(
                    type="string",
                    description="Target host",
                    required=True,
                ),
                "limit": McpToolParam(
                    type="integer",
                    description="Max items",
                    required=False,
                ),
            },
        )
        impl.register_tools([req])
        tools = asyncio.run(impl.list_tools())
        schema = tools[0].inputSchema
        self.assertEqual(schema["properties"]["host"]["type"], "string")
        self.assertEqual(schema["properties"]["host"]["description"], "Target host")
        self.assertEqual(schema["properties"]["limit"]["type"], "integer")
        self.assertEqual(schema["required"], ["host"])
        self.assertNotIn("limit", schema["required"])

    def test_list_tools_builds_input_schema_from_mcp_request_placeholders(self):
        impl = MCPServerImpl()
        req = RequestData(
            name="Echo",
            expose_as_mcp=True,
            method="GET",
            url="http://{{ mcp.request.host }}/p",
            body='{"q": "{{ mcp.request.query }}"}',
        )
        impl.register_tools([req])
        tools = asyncio.run(impl.list_tools())
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0].name, "echo")
        schema = tools[0].inputSchema
        self.assertEqual(schema["type"], "object")
        self.assertIn("host", schema["properties"])
        self.assertIn("query", schema["properties"])
        self.assertEqual(set(schema["required"]), {"host", "query"})

    def test_list_tools_empty_when_no_tools(self):
        impl = MCPServerImpl()
        impl.register_tools([])
        self.assertEqual(asyncio.run(impl.list_tools()), [])

    def test_list_tools_excludes_hidden_env_placeholders_from_schema(self):
        impl = MCPServerImpl(
            hidden_keys_supplier=lambda: {"api_key"},
            variable_supplier=lambda: {"api_key": "secret-value", "base_url": "http://api"},
        )
        req = RequestData(
            name="Auth",
            expose_as_mcp=True,
            method="GET",
            url="{{ base_url }}/items",
            headers={"Authorization": "Bearer {{ api_key }}"},
        )
        impl.register_tools([req])
        schema = asyncio.run(impl.list_tools())[0].inputSchema
        self.assertNotIn("api_key", schema.get("properties", {}))
        self.assertNotIn("base_url", schema.get("properties", {}))

    def test_list_tools_strips_hidden_key_from_explicit_mcp_params(self):
        impl = MCPServerImpl(hidden_keys_supplier=lambda: {"token"})
        req = RequestData(
            name="Auth",
            expose_as_mcp=True,
            method="GET",
            url="http://example.com",
            mcp_params={
                "token": McpToolParam(type="string", required=True),
                "page": McpToolParam(type="integer", required=False),
            },
        )
        impl.register_tools([req])
        schema = asyncio.run(impl.list_tools())[0].inputSchema
        self.assertNotIn("token", schema.get("properties", {}))
        self.assertIn("page", schema.get("properties", {}))

    def test_call_tool_uses_real_hidden_env_values_at_execution(self):
        impl = MCPServerImpl(
            hidden_keys_supplier=lambda: {"api_key"},
            variable_supplier=lambda: {"api_key": "real-secret"},
        )
        req = RequestData(
            name="Auth",
            expose_as_mcp=True,
            method="GET",
            url="http://example.com",
            headers={"Authorization": "Bearer {{ api_key }}"},
        )
        impl.register_tools([req])
        impl.request_service = MagicMock()
        impl.request_service.execute.return_value = _exec_result("ok")
        asyncio.run(impl.call_tool("auth", {}))
        passed_ctx = impl.request_service.execute.call_args[0][1]
        self.assertEqual(passed_ctx["api_key"], "real-secret")

    def test_call_tool_raises_when_unknown(self):
        impl = MCPServerImpl()

        async def _run():
            await impl.call_tool("missing", {})

        with self.assertRaises(ValueError):
            asyncio.run(_run())

    def test_call_tool_invokes_request_service_with_mcp_context(self):
        metrics = MagicMock()
        impl = MCPServerImpl(metrics=metrics)
        req = RequestData(name="Tool", expose_as_mcp=True, method="GET", url="http://u")
        impl.register_tools([req])
        impl.request_service = MagicMock()
        impl.request_service.execute.return_value = _exec_result("response-body")
        out = asyncio.run(impl.call_tool("tool", {"x": "y"}))
        impl.request_service.execute.assert_called_once()
        passed_req, passed_ctx = impl.request_service.execute.call_args[0]
        self.assertIs(passed_req, req)
        self.assertEqual(passed_ctx, {"mcp": {"request": {"x": "y"}}})
        self.assertIsInstance(out[0], TextContent)
        payload = _parse_tool_result(out[0].text)
        self.assertEqual(payload["status"], 200)
        self.assertFalse(payload["error"])
        self.assertEqual(payload["body"], "response-body")
        metrics.track_mcp_request_received.assert_called_once_with("GET")
        metrics.track_mcp_response_sent.assert_called_once_with("GET", "success")
        metrics.track_mcp_tool_call_duration.assert_called_once()
        duration_args = metrics.track_mcp_tool_call_duration.call_args[0]
        self.assertEqual(duration_args[0], "GET")
        self.assertEqual(duration_args[1], "success")
        self.assertGreaterEqual(duration_args[2], 0.0)

    def test_merge_execution_variables_combines_env_and_mcp_args(self):
        merged = _merge_execution_variables(
            {"base_url": "http://api"}, {"id": "1"}
        )
        self.assertEqual(
            merged,
            {"base_url": "http://api", "mcp": {"request": {"id": "1"}}},
        )

    def test_merge_execution_variables_mcp_namespace_wins_over_env_mcp_key(self):
        merged = _merge_execution_variables(
            {"mcp": "env-value", "base_url": "http://api"},
            {"id": "1"},
        )
        self.assertEqual(merged["base_url"], "http://api")
        self.assertEqual(merged["mcp"], {"request": {"id": "1"}})

    def test_call_tool_passes_merged_env_and_mcp_context(self):
        impl = MCPServerImpl(
            variable_supplier=lambda: {"base_url": "http://api"}
        )
        req = RequestData(
            name="Tool",
            expose_as_mcp=True,
            method="GET",
            url="{{ base_url }}/{{ mcp.request.id }}",
        )
        impl.register_tools([req])
        impl.request_service = MagicMock()
        impl.request_service.execute.return_value = _exec_result("ok")
        asyncio.run(impl.call_tool("tool", {"id": "1"}))
        _req, passed_ctx = impl.request_service.execute.call_args[0]
        self.assertEqual(
            passed_ctx,
            {
                "base_url": "http://api",
                "mcp": {"request": {"id": "1"}},
            },
        )

    def test_call_tool_invokes_variable_supplier_per_call(self):
        remaining = [{"base_url": "http://staging"}, {"base_url": "http://prod"}]
        impl = MCPServerImpl(variable_supplier=lambda: remaining.pop(0))
        req = RequestData(name="Tool", expose_as_mcp=True, method="GET", url="http://u")
        impl.register_tools([req])
        impl.request_service = MagicMock()
        impl.request_service.execute.return_value = _exec_result("ok")
        asyncio.run(impl.call_tool("tool", {}))
        asyncio.run(impl.call_tool("tool", {}))
        first_ctx = impl.request_service.execute.call_args_list[0][0][1]
        second_ctx = impl.request_service.execute.call_args_list[1][0][1]
        self.assertEqual(first_ctx["base_url"], "http://staging")
        self.assertEqual(second_ctx["base_url"], "http://prod")

    def test_execute_request_sync_parity_with_request_service(self):
        from pypost.core.http_client import HTTPRequestResult, ResolvedRequestFields
        from pypost.core.request_service import RequestService

        env_vars = {"base_url": "http://api"}
        mcp_args = {"id": "42"}
        req = RequestData(
            name="Parity",
            expose_as_mcp=True,
            method="GET",
            url="{{ base_url }}/items/{{ mcp.request.id }}",
        )
        resolved_url = "http://api/items/42"
        http_result = HTTPRequestResult(
            response=ResponseData(
                status_code=200,
                headers={},
                body="ok",
                elapsed_time=0.01,
                size=2,
            ),
            resolved=ResolvedRequestFields(url=resolved_url, headers={}, body=""),
        )

        direct_svc = RequestService()
        direct_svc.http_client = MagicMock()
        direct_svc.http_client.send_request.return_value = http_result
        merged = _merge_execution_variables(env_vars, mcp_args)
        direct = direct_svc.execute(req, merged)

        impl = MCPServerImpl(variable_supplier=lambda: dict(env_vars))
        impl.request_service = RequestService()
        impl.request_service.http_client = MagicMock()
        impl.request_service.http_client.send_request.return_value = http_result
        via_mcp = impl._execute_request_sync(req, mcp_args)

        direct_url = direct_svc.http_client.send_request.call_args.kwargs.get(
            "variables"
        )
        mcp_url_vars = impl.request_service.http_client.send_request.call_args.kwargs.get(
            "variables"
        )
        self.assertEqual(direct_url, mcp_url_vars)
        self.assertEqual(via_mcp.response.body, direct.response.body)

    def test_call_tool_returns_structured_json_with_script_logs_and_error(self):
        impl = MCPServerImpl()
        req = RequestData(name="T", expose_as_mcp=True, method="GET", url="http://u")
        impl.register_tools([req])
        impl.request_service = MagicMock()
        impl.request_service.execute.return_value = _exec_result(
            "base", logs=["log line"], script_error="bad script"
        )
        out = asyncio.run(impl.call_tool("t", {}))
        payload = _parse_tool_result(out[0].text)
        self.assertEqual(payload["body"], "base")
        self.assertTrue(payload["error"])
        self.assertEqual(payload["logs"], ["log line"])
        self.assertEqual(payload["error_category"], "script")
        self.assertEqual(payload["error_message"], "Post-script execution failed.")

    def test_call_tool_upstream_http_error_is_not_execution_error(self):
        impl = MCPServerImpl()
        req = RequestData(name="T", expose_as_mcp=True, method="GET", url="http://u")
        impl.register_tools([req])
        impl.request_service = MagicMock()
        impl.request_service.execute.return_value = _exec_result(
            "not found", status_code=404
        )
        out = asyncio.run(impl.call_tool("t", {}))
        payload = _parse_tool_result(out[0].text)
        self.assertEqual(payload["status"], 404)
        self.assertFalse(payload["error"])
        self.assertEqual(payload["body"], "not found")

    def test_call_tool_on_execute_exception_returns_error_content_and_metrics(self):
        metrics = MagicMock()
        impl = MCPServerImpl(metrics=metrics)
        req = RequestData(name="T", expose_as_mcp=True, method="POST", url="http://u")
        impl.register_tools([req])
        impl.request_service = MagicMock()
        impl.request_service.execute.side_effect = RuntimeError("execute failed")
        out = asyncio.run(impl.call_tool("t", {}))
        self.assertIn("execute failed", out[0].text)
        self.assertFalse(out[0].text.strip().startswith("{"))
        metrics.track_mcp_response_sent.assert_called_once_with("POST", "error")


class TestStructuredToolResultHelpers(unittest.TestCase):
    def test_tool_result_has_error_when_execution_error_set(self):
        result = _exec_result(script_error="fail")
        self.assertTrue(_tool_result_has_error(result))

    def test_tool_result_has_error_when_status_zero(self):
        result = _exec_result(status_code=0)
        self.assertTrue(_tool_result_has_error(result))

    def test_tool_result_not_error_for_upstream_404(self):
        result = _exec_result("missing", status_code=404)
        self.assertFalse(_tool_result_has_error(result))

    def test_format_structured_tool_result_omits_empty_logs(self):
        text = format_structured_tool_result(_exec_result("ok"))
        payload = json.loads(text)
        self.assertNotIn("logs", payload)
        self.assertEqual(payload["status"], 200)
        self.assertFalse(payload["error"])
        self.assertEqual(payload["body"], "ok")


class TestMcpToolSchemaHelpers(unittest.TestCase):
    def test_tool_description_prefers_mcp_description(self):
        req = RequestData(name="N", mcp_description="  Agent text  ")
        self.assertEqual(tool_description(req), "Agent text")

    def test_tool_description_falls_back_to_name(self):
        req = RequestData(name="Fallback")
        self.assertEqual(tool_description(req), "Fallback")

    def test_resolve_param_specs_merges_discovered_and_explicit(self):
        req = RequestData(
            mcp_params={
                "extra": McpToolParam(type="boolean", required=False),
            }
        )
        specs = resolve_mcp_param_specs(req, {"host"})
        self.assertEqual(specs["host"].type, "string")
        self.assertEqual(specs["extra"].type, "boolean")

    def test_build_tool_input_schema_omits_empty_description(self):
        schema = build_tool_input_schema(
            {"id": McpToolParam(type="string", description="")}
        )
        self.assertNotIn("description", schema["properties"]["id"])


class TestMCPServerImplRouting(unittest.TestCase):
    def test_create_app_returns_starlette_application(self):
        app = MCPServerImpl().create_app()
        self.assertIsInstance(app, Starlette)

    def test_create_app_exposes_streamable_http_route(self):
        app = MCPServerImpl().create_app()
        route_paths = [route.path for route in app.routes if isinstance(route, Route)]
        self.assertIn(MCP_STREAMABLE_HTTP_PATH, route_paths)

    def test_create_app_mounts_sse_sub_application_for_backward_compat(self):
        app = MCPServerImpl().create_app()
        mounts = [route for route in app.routes if isinstance(route, Mount)]
        self.assertEqual(len(mounts), 1)
        self.assertEqual(mounts[0].path, MCP_LEGACY_SSE_MOUNT_PATH)

    def test_inner_sse_app_exposes_messages_mount_and_get_root(self):
        app = MCPServerImpl().create_app()
        sse_mount = next(route for route in app.routes if isinstance(route, Mount))
        inner_paths = []
        for route in sse_mount.app.routes:
            if isinstance(route, Mount):
                inner_paths.append(("mount", route.path))
            elif isinstance(route, Route):
                inner_paths.append(("route", route.path, route.methods))
        self.assertIn(
            ("mount", MCP_LEGACY_SSE_MESSAGES_PATH),
            [(p[0], p[1]) for p in inner_paths],
        )
        get_roots = [
            p for p in inner_paths if p[0] == "route" and "GET" in p[2] and p[1] == "/"
        ]
        self.assertEqual(len(get_roots), 1)

    def test_routing_rejects_wrong_http_methods_without_live_transport(self):
        client = TestClient(MCPServerImpl().create_app(), raise_server_exceptions=False)
        self.assertEqual(
            client.post(MCP_LEGACY_SSE_MOUNT_PATH).status_code,
            405,
        )
        self.assertEqual(
            client.get(
                f"{MCP_LEGACY_SSE_MOUNT_PATH}{MCP_LEGACY_SSE_MESSAGES_PATH}"
            ).status_code,
            405,
        )
        self.assertEqual(client.get("/unknown").status_code, 404)


class TestMCPServerImplInjection(unittest.TestCase):
    def test_injected_template_service_is_used_for_schema_generation(self):
        """A TemplateService passed at construction is used during list_tools."""
        mock_ts = MagicMock()
        mock_ts.parse.return_value = MagicMock()
        impl = MCPServerImpl(template_service=mock_ts)
        req = RequestData(
            name="Echo",
            expose_as_mcp=True,
            method="GET",
            url="http://{{ mcp.request.host }}/p",
        )
        impl.register_tools([req])
        asyncio.run(impl.list_tools())
        mock_ts.parse.assert_called()


if __name__ == "__main__":
    unittest.main()
