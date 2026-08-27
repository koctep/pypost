from __future__ import annotations

import asyncio
import errno
import logging
import socket
import sys
import threading
import time
from collections.abc import Callable, Sequence

import uvicorn
from PySide6.QtCore import QObject, Signal

from pypost.core.mcp_activity_log import McpActivityEntry, McpActivityLog
from pypost.core.mcp_proxy_server_impl import MCPProxyServerImpl
from pypost.core.mcp_server_impl import MCPServerImpl
from pypost.core.metrics_protocol import MetricsTrackerProtocol
from pypost.core.server_bind import (
    drain_pending_tasks,
    format_bind_error,
    get_process_exit_original,
    install_thread_exit,
    uninstall_thread_exit,
)
from pypost.core.template_service import TemplateService
from pypost.models.models import RequestData
from pypost.models.websocket import WebSocketConnection


logger = logging.getLogger(__name__)


def mcp_tools_signature(
    tools: Sequence[RequestData | WebSocketConnection],
) -> tuple[tuple[str, str], ...]:
    """Stable fingerprint of exposed MCP tools for change detection."""
    exposed = ((req.id, req.name) for req in tools if req.expose_as_mcp)
    return tuple(sorted(exposed))


def format_mcp_bind_error(exc: OSError, host: str, port: int) -> str:
    """Return an operator-facing message for MCP bind failures."""
    return format_bind_error(exc, host, port, "MCP server")


class MCPServerManager(QObject):
    status_changed = Signal(bool)  # True = running, False = stopped
    start_failed = Signal(str)  # operator-facing bind / startup error
    activity_recorded = Signal(object)  # payload: McpActivityEntry

    def __init__(
        self,
        metrics: MetricsTrackerProtocol | None = None,
        template_service: TemplateService | None = None,
    ):
        super().__init__()
        self._server_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._server_instance: uvicorn.Server | None = None
        self._metrics = metrics
        self._template_service = template_service
        self._activity_log = McpActivityLog(on_append=self._emit_activity)
        self._impl: MCPServerImpl | MCPProxyServerImpl = MCPServerImpl(
            metrics=metrics,
            template_service=template_service,
            activity_log=self._activity_log,
        )
        if template_service is not None:
            logger.debug(
                "MCPServerManager: propagating TemplateService id=%d", id(template_service)
            )
        self._current_port = 1080
        self._current_host = "127.0.0.1"
        self._variable_supplier: Callable[[], dict[str, str]] | None = None
        self._hidden_keys_supplier: Callable[[], set[str]] | None = None
        self._startup_notified = False
        self._start_error: str | None = None
        self._tools_signature: tuple[tuple[str, str], ...] = ()

    @property
    def activity_log(self) -> McpActivityLog:
        return self._activity_log

    @property
    def last_start_error(self) -> str | None:
        """Latest asynchronous startup failure, if this manager could not bind."""
        return self._start_error

    @property
    def is_listening(self) -> bool:
        """Whether the server completed startup and is accepting connections."""
        return self._startup_notified

    def _emit_activity(self, entry: McpActivityEntry) -> None:
        self.activity_recorded.emit(entry)

    def set_variable_supplier(
        self, supplier: Callable[[], dict[str, str]] | None
    ) -> None:
        self._variable_supplier = supplier
        self._impl.set_variable_supplier(supplier)

    def set_hidden_keys_supplier(
        self, supplier: Callable[[], set[str]] | None
    ) -> None:
        self._hidden_keys_supplier = supplier
        self._impl.set_hidden_keys_supplier(supplier)

    def start_server(
        self,
        port: int,
        tools: Sequence[RequestData | WebSocketConnection],
        host: str = "127.0.0.1",
    ):
        if self.is_running():
            self.stop_server()

        if not isinstance(self._impl, MCPServerImpl):
            self._impl = MCPServerImpl(
                metrics=self._metrics,
                template_service=self._template_service,
                activity_log=self._activity_log,
                variable_supplier=self._variable_supplier,
                hidden_keys_supplier=self._hidden_keys_supplier,
            )

        self._current_port = port
        self._current_host = host
        self._tools_signature = mcp_tools_signature(tools)
        self._impl.register_tools(tools)
        self._stop_event.clear()
        self._startup_notified = False
        self._start_error = None

        self._server_thread = threading.Thread(target=self._run_uvicorn, daemon=True)
        self._server_thread.start()
        logger.info("MCP server starting on %s:%d", host, port)

    def start_proxy_server(
        self,
        port: int,
        upstream_url: str,
        upstream_transport: str = "streamable_http",
        headers: dict[str, str] | None = None,
        host: str = "127.0.0.1",
        name: str = "pypost-proxy",
        timeout: float = 30.0,
    ) -> None:
        if self.is_running():
            self.stop_server()

        self._current_port = port
        self._current_host = host
        self._tools_signature = ()
        self._impl = MCPProxyServerImpl(
            name=name,
            upstream_url=upstream_url,
            upstream_transport=upstream_transport,  # type: ignore[arg-type]
            headers=headers or {},
            timeout=timeout,
            variable_supplier=self._variable_supplier,
            hidden_keys_supplier=self._hidden_keys_supplier,
            activity_log=self._activity_log,
            metrics=self._metrics,
            template_service=self._template_service,
        )
        self._stop_event.clear()
        self._startup_notified = False
        self._start_error = None

        self._server_thread = threading.Thread(target=self._run_uvicorn, daemon=True)
        self._server_thread.start()
        logger.info("MCP proxy server starting on %s:%d", host, port)

    def stop_server(self):
        if not self.is_running():
            return

        self._stop_event.set()
        if self._server_instance:
            self._server_instance.should_exit = True

        if self._server_thread:
            # Wait for thread to finish (with timeout to avoid freeze).
            # Keep the ref if join times out so is_running() stays truthful while
            # the orphaned worker still holds the listen socket (PYPOST-1196).
            self._server_thread.join(timeout=2.0)
            if not self._server_thread.is_alive():
                self._server_thread = None

        self._server_instance = None
        logger.info("MCP server stopped")
        self.status_changed.emit(False)

    def is_running(self) -> bool:
        return self._server_thread is not None and self._server_thread.is_alive()

    def update_tools(self, tools: list[RequestData]) -> bool:
        """Restart the server when the exposed tool set changes. Returns True if restarted."""
        signature = mcp_tools_signature(tools)
        if signature == self._tools_signature:
            return False
        self._tools_signature = signature
        if not self.is_running():
            return False
        logger.info("mcp_tools_changed tool_count=%d restarting=true", len(signature))
        self.stop_server()
        self._wait_until_port_bindable()
        if self._server_thread is not None and not self._server_thread.is_alive():
            self._server_thread = None
        self.start_server(self._current_port, tools, self._current_host)
        return True

    def _wait_until_port_bindable(self, timeout: float = 10.0) -> None:
        """Wait until the current host/port can be bound again after stop_server."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.is_running():
                time.sleep(0.05)
                continue
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    sock.bind((self._current_host, self._current_port))
                return
            except OSError:
                time.sleep(0.05)
        logger.warning(
            "mcp_port_still_busy host=%s port=%d",
            self._current_host,
            self._current_port,
        )

    def _notify_started(self) -> None:
        if self._startup_notified or self._stop_event.is_set():
            return
        self._startup_notified = True
        logger.info(
            "mcp_server_listening host=%s port=%d",
            self._current_host,
            self._current_port,
        )
        self.status_changed.emit(True)

    def _notify_start_failed(self, message: str) -> None:
        self._start_error = message
        logger.error(
            "mcp_server_start_failed host=%s port=%d message=%s",
            self._current_host,
            self._current_port,
            message,
        )
        self.start_failed.emit(message)
        self.status_changed.emit(False)

    def _run_uvicorn(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        def thread_exit(code=0):
            if code != 0:
                raise OSError(
                    errno.EADDRINUSE,
                    f"bind failed on {self._current_host}:{self._current_port}",
                )
            original = get_process_exit_original() or sys.exit
            return original(code)

        install_thread_exit(thread_exit)
        try:
            app = self._impl.create_app()
            config = uvicorn.Config(
                app=app,
                host=self._current_host,
                port=self._current_port,
                loop="asyncio",
                log_config=None,
                log_level="warning",
            )
            self._server_instance = uvicorn.Server(config)

            # Override install_signal_handlers because we are not in main thread
            self._server_instance.install_signal_handlers = lambda: None

            original_startup = self._server_instance.startup

            async def startup_with_notify(sockets=None):
                await original_startup(sockets=sockets)
                self._notify_started()

            self._server_instance.startup = startup_with_notify

            loop.run_until_complete(self._server_instance.serve())
        except OSError as exc:
            self._notify_start_failed(
                format_mcp_bind_error(exc, self._current_host, self._current_port)
            )
        except Exception as exc:
            logger.exception("mcp_server_start_failed")
            self._notify_start_failed(f"MCP server failed to start: {exc}")
        finally:
            uninstall_thread_exit()
            drain_pending_tasks(loop)
            loop.close()

            if not self._stop_event.is_set() and not self._startup_notified:
                self.status_changed.emit(False)
            elif not self._stop_event.is_set() and self._startup_notified:
                logger.warning("mcp_server_unexpected_exit")
                self.status_changed.emit(False)
