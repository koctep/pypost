"""Live MCP integration tests for the committed MCP test collection (PYPOST-181)."""
import pytest

import json
import unittest
from unittest.mock import MagicMock

import anyio
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.shared._httpx_utils import create_mcp_http_client

from pypost.core.mcp_tools_overview import collect_mcp_tool_overview
from pypost.core.request_service import ExecutionResult
from pypost.models.response import ResponseData
from tests.helpers.mcp_live_server import live_mcp_server
from tests.helpers.mcp_test_collection import (
    EXPECTED_MCP_TOOL_NAMES,
    load_mcp_test_collection,
    mcp_exposed_requests,
)

pytestmark = pytest.mark.timeout(120)


def _exec_result(body: str = "ok", status_code: int = 200) -> ExecutionResult:
    return ExecutionResult(
        response=ResponseData(
            status_code=status_code,
            headers={},
            body=body,
            elapsed_time=0.01,
            size=len(body.encode("utf-8")),
        ),
        updated_variables={},
        script_logs=[],
        execution_error=None,
    )


async def _mcp_list_tools(mcp_url: str) -> list[str]:
    async with create_mcp_http_client() as http_client:
        async with streamable_http_client(mcp_url, http_client=http_client) as (
            read,
            write,
            _,
        ):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.list_tools()
                return [tool.name for tool in result.tools]


async def _mcp_call_tool(mcp_url: str, name: str, arguments: dict | None = None) -> dict:
    async with create_mcp_http_client() as http_client:
        async with streamable_http_client(mcp_url, http_client=http_client) as (
            read,
            write,
            _,
        ):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(name, arguments or {})
                return json.loads(result.content[0].text)


@pytest.mark.timeout(120)
def test_list_tools_over_live_streamable_http(mcp_collection_live_server):
    collection = load_mcp_test_collection()
    tools = mcp_exposed_requests()
    names = anyio.run(_mcp_list_tools, mcp_collection_live_server.mcp_url)
    assert set(names) == EXPECTED_MCP_TOOL_NAMES
    assert len(collection.requests) - len(tools) == 1


class TestMcpTestCollectionIntegration(unittest.TestCase):
    def test_collection_exposes_expected_mcp_tools(self):
        collection = load_mcp_test_collection()
        tools = mcp_exposed_requests()
        tool_names = {
            entry.mcp_name for entry in collect_mcp_tool_overview([collection])
        }
        self.assertEqual(len(tools), len(EXPECTED_MCP_TOOL_NAMES))
        self.assertEqual(tool_names, EXPECTED_MCP_TOOL_NAMES)

    def test_call_tool_for_each_exposed_collection_request(self):
        tools = mcp_exposed_requests()
        with live_mcp_server(tools, execute_result=_exec_result("probe-ok")) as server:
            for tool_name in sorted(EXPECTED_MCP_TOOL_NAMES):
                payload = anyio.run(_mcp_call_tool, server.mcp_url, tool_name, {})
                self.assertFalse(payload["error"])
                self.assertEqual(payload["status"], 200)
                self.assertEqual(payload["body"], "probe-ok")

    def test_call_tool_executes_matching_collection_request(self):
        tools = mcp_exposed_requests()
        by_name = {request.name: request for request in tools}
        with live_mcp_server(tools, execute_result=_exec_result("matched")) as server:
            anyio.run(_mcp_call_tool, server.mcp_url, "sse_probe_metrics", {})
            server._mock_request_service.execute.assert_called_once()
            executed_request, _ctx = server._mock_request_service.execute.call_args[0]
            self.assertEqual(executed_request.name, by_name["SSE Probe Metrics"].name)
            self.assertEqual(executed_request.url, by_name["SSE Probe Metrics"].url)


if __name__ == "__main__":
    unittest.main()
