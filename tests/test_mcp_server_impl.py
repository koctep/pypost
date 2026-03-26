"""Tests for MCPServerImpl: tool registration, schemas, and call_tool execution path."""
import asyncio
import unittest
from unittest.mock import MagicMock

from mcp.types import TextContent

from pypost.core.mcp_server_impl import MCPServerImpl
from pypost.core.request_service import ExecutionResult
from pypost.models.models import RequestData
from pypost.models.response import ResponseData


def _exec_result(body="ok", logs=None, script_error=None):
    return ExecutionResult(
        response=ResponseData(
            status_code=200,
            headers={},
            body=body,
            elapsed_time=0.01,
            size=len(body.encode("utf-8")),
        ),
        updated_variables={},
        script_logs=logs or [],
        script_error=script_error,
    )


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
        self.assertEqual(out[0].text, "response-body")
        metrics.track_mcp_request_received.assert_called_once_with("GET")
        metrics.track_mcp_response_sent.assert_called_once_with("GET", "success")

    def test_call_tool_appends_script_logs_and_error_to_body(self):
        impl = MCPServerImpl()
        req = RequestData(name="T", expose_as_mcp=True, method="GET", url="http://u")
        impl.register_tools([req])
        impl.request_service = MagicMock()
        impl.request_service.execute.return_value = _exec_result(
            "base", logs=["log line"], script_error="bad script"
        )
        out = asyncio.run(impl.call_tool("t", {}))
        text = out[0].text
        self.assertIn("base", text)
        self.assertIn("Script Logs", text)
        self.assertIn("log line", text)
        self.assertIn("Script Error", text)
        self.assertIn("bad script", text)

    def test_call_tool_on_execute_exception_returns_error_content_and_metrics(self):
        metrics = MagicMock()
        impl = MCPServerImpl(metrics=metrics)
        req = RequestData(name="T", expose_as_mcp=True, method="POST", url="http://u")
        impl.register_tools([req])
        impl.request_service = MagicMock()
        impl.request_service.execute.side_effect = RuntimeError("execute failed")
        out = asyncio.run(impl.call_tool("t", {}))
        self.assertIn("execute failed", out[0].text)
        metrics.track_mcp_response_sent.assert_called_once_with("POST", "error")


if __name__ == "__main__":
    unittest.main()
