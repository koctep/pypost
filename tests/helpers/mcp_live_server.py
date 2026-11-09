"""Shared live MCP uvicorn harness for integration tests (PYPOST-592)."""

from __future__ import annotations

import asyncio
import logging
import socket
import threading
import time
from contextlib import contextmanager
from unittest.mock import MagicMock

import uvicorn

from pypost.core.mcp_server_impl import MCPServerImpl
from pypost.core.request_service import ExecutionResult
from pypost.core.server_bind import drain_pending_tasks
from tests.helpers.port_allocation import allocate_bound_tcp_socket, allocate_tcp_port

logger = logging.getLogger(__name__)

_MAX_BIND_ATTEMPTS = 5
_BIND_READY_TIMEOUT_SEC = 2.0


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
        self.port = 0
        self._listen_sock: socket.socket | None = None
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
        last_error: BaseException | None = None
        for attempt in range(1, _MAX_BIND_ATTEMPTS + 1):
            self.stop()
            self._listen_sock = allocate_bound_tcp_socket(self.host)
            self.port = int(self._listen_sock.getsockname()[1])
            self._thread = threading.Thread(target=self._run_uvicorn, daemon=True)
            self._thread.start()
            try:
                wait_for_port(self.host, self.port, timeout=_BIND_READY_TIMEOUT_SEC)
                if attempt > 1:
                    logger.info(
                        "mcp_live_server_bind_retry_succeeded attempt=%d port=%d",
                        attempt,
                        self.port,
                    )
                return
            except TimeoutError as exc:
                last_error = exc
                logger.warning(
                    "mcp_live_server_bind_retry attempt=%d port=%d error=%s",
                    attempt,
                    self.port,
                    exc,
                )
                self.stop()
        raise TimeoutError(
            f"MCP server failed to listen on {self.host} after "
            f"{_MAX_BIND_ATTEMPTS} bind attempts"
        ) from last_error

    def stop(self) -> None:
        if self._server is not None:
            self._server.should_exit = True
        if self._thread is not None:
            self._thread.join(timeout=3.0)
        self._thread = None
        self._server = None
        if self._listen_sock is not None:
            try:
                self._listen_sock.close()
            except OSError:
                pass
            self._listen_sock = None

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
        sockets = [self._listen_sock] if self._listen_sock is not None else None
        try:
            loop.run_until_complete(self._server.serve(sockets=sockets))
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
