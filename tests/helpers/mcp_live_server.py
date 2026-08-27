"""Shared live MCP uvicorn harness for integration tests (PYPOST-592)."""

from __future__ import annotations

import asyncio
import socket
import threading
import time
from contextlib import contextmanager
from unittest.mock import MagicMock

import uvicorn

from pypost.core.mcp_server_impl import MCPServerImpl
from pypost.core.request_service import ExecutionResult
from pypost.core.server_bind import drain_pending_tasks
from tests.helpers.port_allocation import allocate_tcp_port


def free_port() -> int:
    return allocate_tcp_port("127.0.0.1")


def wait_for_port(host: str, port: int, timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.05)
    raise TimeoutError(f"MCP server did not listen on {host}:{port} within {timeout}s")


class LiveMCPServer:
    """Minimal uvicorn harness mirroring MCPServerManager._run_uvicorn."""

    def __init__(self, tools, execute_result: ExecutionResult | None = None):
        self.host = "127.0.0.1"
        self.port = free_port()
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
        wait_for_port(self.host, self.port)

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
            app=app,
            host=self.host,
            port=self.port,
            loop="asyncio",
            log_config=None,
            log_level="warning",
        )
        self._server = uvicorn.Server(config)
        self._server.install_signal_handlers = lambda: None
        try:
            loop.run_until_complete(self._server.serve())
        finally:
            drain_pending_tasks(loop)
            loop.close()


@contextmanager
def live_mcp_server(tools, execute_result: ExecutionResult | None = None):
    server = LiveMCPServer(tools, execute_result=execute_result)
    server.start()
    try:
        yield server
    finally:
        server.stop()
