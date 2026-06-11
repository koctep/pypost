"""Integration tests: live MCP server over Streamable HTTP round-trip (PYPOST-368/551)."""
import pytest

pytestmark = pytest.mark.timeout(120)

import asyncio
import json
import socket
import threading
import time
import unittest
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import MagicMock

import anyio
import uvicorn
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.shared._httpx_utils import create_mcp_http_client

from pypost.core.mcp_client_service import MCPClientService
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
    """Minimal uvicorn harness mirroring MCPServerManager._run_uvicorn."""

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


class TestMCPServerIntegration(unittest.TestCase):
    def test_mcp_client_service_list_tools_over_live_streamable_http(self):
        """MCPClientService sync wrapper works against live server (PYPOST-560)."""
        tool = RequestData(
            name="Echo Tool",
            expose_as_mcp=True,
            method="GET",
            url="http://example.com/{{ mcp.request.msg }}",
        )
        with live_mcp_server([tool]) as server:
            service = MCPClientService()
            result = service.run(server.mcp_url, "list_tools", None)

        self.assertEqual(result.status_code, 200)
        body = json.loads(result.body)
        self.assertEqual([t["name"] for t in body["tools"]], ["echo_tool"])

    def test_list_tools_over_live_streamable_http(self):
        tool = RequestData(
            name="Echo Tool",
            expose_as_mcp=True,
            method="GET",
            url="http://example.com/{{ mcp.request.msg }}",
        )
        with live_mcp_server([tool]) as server:
            names = anyio.run(_mcp_list_tools, server.mcp_url)
            self.assertEqual(names, ["echo_tool"])

    def test_call_tool_over_live_streamable_http_returns_response_body(self):
        tool = RequestData(
            name="Ping",
            expose_as_mcp=True,
            method="GET",
            url="http://example.com/ping",
        )
        with live_mcp_server([tool], execute_result=_exec_result("pong")) as server:
            payload = anyio.run(_mcp_call_tool, server.mcp_url, "ping", {})
            self.assertFalse(payload["error"])
            self.assertEqual(payload["status"], 200)
            self.assertEqual(payload["body"], "pong")

    def test_call_tool_passes_mcp_arguments_to_request_service(self):
        tool = RequestData(
            name="Greet",
            expose_as_mcp=True,
            method="GET",
            url="http://example.com/{{ mcp.request.name }}",
        )
        with live_mcp_server([tool], execute_result=_exec_result("hello")) as server:
            anyio.run(_mcp_call_tool, server.mcp_url, "greet", {"name": "world"})
            server._mock_request_service.execute.assert_called_once()
            _req, ctx = server._mock_request_service.execute.call_args[0]
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
            anyio.run(_mcp_call_tool, server.mcp_url, "fetch", {"id": "1"})
            _req, ctx = server._mock_request_service.execute.call_args[0]
            self.assertEqual(
                ctx,
                {
                    "base_url": "http://api",
                    "mcp": {"request": {"id": "1"}},
                },
            )
        finally:
            server.stop()

    def test_call_tool_executes_real_outbound_http_via_stub(self):
        """MCP tool call hits a local HTTP stub (PYPOST-564), not mocked execute."""
        stub_port = _free_port()
        stub_body = "stub-response"

        class _StubHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                payload = stub_body.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, _format, *_args):
                return

        httpd = ThreadingHTTPServer(("127.0.0.1", stub_port), _StubHandler)
        server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        server_thread.start()
        try:
            tool = RequestData(
                name="Stub Echo",
                expose_as_mcp=True,
                method="GET",
                url=f"http://127.0.0.1:{stub_port}/echo",
            )
            with live_mcp_server([tool]) as mcp_server:
                payload = anyio.run(_mcp_call_tool, mcp_server.mcp_url, "stub_echo", {})
            self.assertFalse(payload["error"])
            self.assertEqual(payload["status"], 200)
            self.assertEqual(payload["body"], stub_body)
        finally:
            httpd.shutdown()
            server_thread.join(timeout=2.0)


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
        mock_svc = MagicMock()
        mock_svc.execute.return_value = _exec_result("from-manager")
        manager._impl._create_request_service = lambda: mock_svc
        manager.start_server(port, [tool], host="127.0.0.1")
        try:
            _wait_for_port("127.0.0.1", port)
            mcp_url = f"http://127.0.0.1:{port}/mcp"
            payload = anyio.run(_mcp_call_tool, mcp_url, "mgr_tool", {})
            self.assertEqual(payload["body"], "from-manager")
            self.assertFalse(payload["error"])
            self.assertTrue(manager.is_running())
        finally:
            manager.stop_server()
            self.assertFalse(manager.is_running())


if __name__ == "__main__":
    unittest.main()
