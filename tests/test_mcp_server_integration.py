"""Integration tests: live MCP server over SSE with MCP client round-trip (PYPOST-368)."""
import pytest

pytestmark = pytest.mark.timeout(120)

import asyncio
import socket
import threading
import time
import unittest
from contextlib import contextmanager
from unittest.mock import MagicMock

import anyio
import uvicorn
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

from pypost.core.mcp_server import MCPServerManager
from pypost.core.mcp_server_impl import MCPServerImpl
from pypost.core.request_service import ExecutionResult
from pypost.models.models import RequestData
from pypost.models.response import ResponseData


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


def _exec_result(body: str = "ok") -> ExecutionResult:
    return ExecutionResult(
        response=ResponseData(
            status_code=200,
            headers={},
            body=body,
            elapsed_time=0.01,
            size=len(body.encode("utf-8")),
        ),
        updated_variables={},
        script_logs=[],
        execution_error=None,
    )


async def _mcp_list_tools(sse_url: str) -> list[str]:
    async with sse_client(sse_url, timeout=3, sse_read_timeout=15) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            return [tool.name for tool in result.tools]


async def _mcp_call_tool(sse_url: str, name: str, arguments: dict | None = None) -> str:
    async with sse_client(sse_url, timeout=3, sse_read_timeout=15) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(name, arguments or {})
            return result.content[0].text


class _LiveMCPServer:
    """Minimal uvicorn harness mirroring MCPServerManager._run_uvicorn."""

    def __init__(self, tools, execute_result: ExecutionResult | None = None):
        self.host = "127.0.0.1"
        self.port = _free_port()
        self.impl = MCPServerImpl()
        self.impl.register_tools(tools)
        if execute_result is not None:
            self.impl.request_service = MagicMock()
            self.impl.request_service.execute.return_value = execute_result
        self._thread: threading.Thread | None = None
        self._server: uvicorn.Server | None = None

    @property
    def sse_url(self) -> str:
        return f"http://{self.host}:{self.port}/sse/"

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


class TestMCPServerIntegration(unittest.TestCase):
    def test_list_tools_over_live_sse(self):
        tool = RequestData(
            name="Echo Tool",
            expose_as_mcp=True,
            method="GET",
            url="http://example.com/{{ mcp.request.msg }}",
        )
        with live_mcp_server([tool]) as server:
            names = anyio.run(_mcp_list_tools, server.sse_url)
            self.assertEqual(names, ["echo_tool"])

    def test_call_tool_over_live_sse_returns_response_body(self):
        tool = RequestData(
            name="Ping",
            expose_as_mcp=True,
            method="GET",
            url="http://example.com/ping",
        )
        with live_mcp_server([tool], execute_result=_exec_result("pong")) as server:
            text = anyio.run(_mcp_call_tool, server.sse_url, "ping", {})
            self.assertIn("pong", text)

    def test_call_tool_passes_mcp_arguments_to_request_service(self):
        tool = RequestData(
            name="Greet",
            expose_as_mcp=True,
            method="GET",
            url="http://example.com/{{ mcp.request.name }}",
        )
        with live_mcp_server([tool], execute_result=_exec_result("hello")) as server:
            anyio.run(_mcp_call_tool, server.sse_url, "greet", {"name": "world"})
            server.impl.request_service.execute.assert_called_once()
            _req, ctx = server.impl.request_service.execute.call_args[0]
            self.assertEqual(ctx, {"mcp": {"request": {"name": "world"}}})

    def test_call_tool_passes_env_and_mcp_variables_to_request_service(self):
        tool = RequestData(
            name="Fetch",
            expose_as_mcp=True,
            method="GET",
            url="{{ base_url }}/{{ mcp.request.id }}",
        )
        server = _LiveMCPServer([tool], execute_result=_exec_result("ok"))
        server.impl.set_variable_supplier(lambda: {"base_url": "http://api"})
        server.start()
        try:
            anyio.run(_mcp_call_tool, server.sse_url, "fetch", {"id": "1"})
            _req, ctx = server.impl.request_service.execute.call_args[0]
            self.assertEqual(
                ctx,
                {
                    "base_url": "http://api",
                    "mcp": {"request": {"id": "1"}},
                },
            )
        finally:
            server.stop()


class TestMCPServerManagerIntegration(unittest.TestCase):
    """Exercise production MCPServerManager thread + uvicorn lifecycle."""

    def test_manager_starts_server_and_invokes_tool(self):
        port = _free_port()
        tool = RequestData(
            name="Mgr Tool",
            expose_as_mcp=True,
            method="GET",
            url="http://example.com/m",
        )
        manager = MCPServerManager()
        manager._impl.request_service = MagicMock()
        manager._impl.request_service.execute.return_value = _exec_result("from-manager")
        manager.start_server(port, [tool], host="127.0.0.1")
        try:
            _wait_for_port("127.0.0.1", port)
            sse_url = f"http://127.0.0.1:{port}/sse/"
            text = anyio.run(_mcp_call_tool, sse_url, "mgr_tool", {})
            self.assertIn("from-manager", text)
            self.assertTrue(manager.is_running())
        finally:
            manager.stop_server()
            self.assertFalse(manager.is_running())


if __name__ == "__main__":
    unittest.main()
