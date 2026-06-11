"""Live MCP integration tests for the committed MCP test collection (PYPOST-181)."""
import pytest

pytestmark = pytest.mark.timeout(120)

import asyncio
import json
import socket
import threading
import time
import unittest
from contextlib import contextmanager
from unittest.mock import MagicMock

import anyio
import uvicorn
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.shared._httpx_utils import create_mcp_http_client

from pypost.core.mcp_server_impl import MCPServerImpl
from pypost.core.mcp_tools_overview import collect_mcp_tool_overview
from pypost.core.request_service import ExecutionResult
from pypost.models.response import ResponseData
from tests.helpers.mcp_test_collection import (
    EXPECTED_MCP_TOOL_NAMES,
    load_mcp_test_collection,
    mcp_exposed_requests,
)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_for_port(host: str, port: int, timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.05)
    raise TimeoutError(f"MCP server did not listen on {host}:{port} within {timeout}s")


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


class _LiveMCPServer:
    """Minimal uvicorn harness for collection-derived MCP tools."""

    def __init__(self, tools, execute_result: ExecutionResult | None = None):
        self.host = "127.0.0.1"
        self.port = _free_port()
        self.impl = MCPServerImpl()
        self.impl.register_tools(tools)
        if execute_result is not None:
            mock_svc = MagicMock()
            mock_svc.execute.return_value = execute_result
            self.impl._create_request_service = lambda: mock_svc
            self._mock_request_service = mock_svc
        self._thread: threading.Thread | None = None
        self._server: uvicorn.Server | None = None

    @property
    def mcp_url(self) -> str:
        return f"http://{self.host}:{self.port}/mcp"

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run_uvicorn, daemon=True)
        self._thread.start()
        _wait_for_port(self.host, self.port)

    def stop(self) -> None:
        if self._server is not None:
            self._server.should_exit = True
        if self._thread is not None:
            self._thread.join(timeout=3.0)

    def _run_uvicorn(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        app = self.impl.create_app()
        config = uvicorn.Config(
            app=app, host=self.host, port=self.port, loop="asyncio", log_level="warning"
        )
        self._server = uvicorn.Server(config)
        self._server.install_signal_handlers = lambda: None
        loop.run_until_complete(self._server.serve())


@contextmanager
def live_mcp_server(tools, execute_result: ExecutionResult | None = None):
    server = _LiveMCPServer(tools, execute_result=execute_result)
    server.start()
    try:
        yield server
    finally:
        server.stop()


class TestMcpTestCollectionIntegration(unittest.TestCase):
    def test_collection_exposes_expected_mcp_tools(self):
        collection = load_mcp_test_collection()
        tools = mcp_exposed_requests()
        tool_names = {
            entry.mcp_name for entry in collect_mcp_tool_overview([collection])
        }
        self.assertEqual(len(tools), len(EXPECTED_MCP_TOOL_NAMES))
        self.assertEqual(tool_names, EXPECTED_MCP_TOOL_NAMES)

    def test_list_tools_over_live_streamable_http(self):
        collection = load_mcp_test_collection()
        tools = mcp_exposed_requests()
        with live_mcp_server(tools) as server:
            names = anyio.run(_mcp_list_tools, server.mcp_url)
            self.assertEqual(set(names), EXPECTED_MCP_TOOL_NAMES)
            self.assertEqual(len(collection.requests) - len(tools), 1)

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
