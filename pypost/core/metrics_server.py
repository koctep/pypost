"""Metrics HTTP/MCP server lifecycle (uvicorn thread)."""
from __future__ import annotations

import asyncio
import errno
import logging
import sys
import threading
from collections.abc import Callable
from dataclasses import dataclass, field


import uvicorn
from mcp.server import Server
from mcp.types import Resource, TextResourceContents
from prometheus_client import generate_latest, make_asgi_app
from starlette.applications import Starlette
from starlette.routing import Mount

from pypost.core.bind_address_validation import is_localhost_bind_host
from pypost.core.mcp_legacy_sse import build_legacy_sse_app
from pypost.core.mcp_streamable_http import build_streamable_http_route
from pypost.core.mcp_transport_routes import MCP_LEGACY_SSE_MOUNT_PATH
from pypost.core.metrics_registry import MetricsRegistry
from pypost.core.server_bind import (
    drain_pending_tasks,
    format_bind_error,
    get_process_exit_original,
    install_thread_exit,
    uninstall_thread_exit,
)

logger = logging.getLogger(__name__)

_install_thread_exit = install_thread_exit
_uninstall_thread_exit = uninstall_thread_exit


@dataclass
class _ServerGeneration:
    number: int
    host: str
    port: int
    stop_event: threading.Event
    startup_notified: bool = False
    server_instance: uvicorn.Server | None = None
    thread: threading.Thread | None = None
    start_failed_handler: Callable[[str], None] | None = None
    listening_changed: Callable[[bool], None] = lambda _value: None
    unexpected_exit: Callable[[str], None] = lambda _reason: None
    callback_lock: threading.RLock = field(default_factory=threading.RLock)
    callbacks_open: bool = True


class MetricsServer:
    """Owns observability MCP resources and uvicorn server lifecycle."""

    def __init__(self, registry: MetricsRegistry) -> None:
        self._registry = registry
        self.server_instance: uvicorn.Server | None = None
        self.thread: threading.Thread | None = None
        self.server_lock = threading.RLock()
        self._current_host = "127.0.0.1"
        self._current_port = 9080
        self._stop_event = threading.Event()
        self._startup_notified = False
        self._start_failed_handler: Callable[[str], None] | None = None
        self._pending_start_failure: str | None = None
        self._is_listening = False
        self._listening_changed: Callable[[bool], None] = lambda _value: None
        self._unexpected_exit: Callable[[str], None] = lambda _reason: None
        self._generation_number = 0
        self._active_generation: _ServerGeneration | None = None

        self.mcp_server = Server("pypost-metrics")
        self.mcp_server.list_resources()(self.list_resources)
        self.mcp_server.read_resource()(self._mcp_read_resource)

    def set_start_failed_handler(
        self, handler: Callable[[str], None] | None
    ) -> None:
        """Register a callback for bind/startup failures (may run off main thread)."""
        self._start_failed_handler = handler
        with self.server_lock:
            if self._active_generation is not None:
                self._active_generation.start_failed_handler = handler
        pending = self._pending_start_failure
        if pending is not None and handler is not None:
            self._pending_start_failure = None
            handler(pending)

    @property
    def is_listening(self) -> bool:
        with self.server_lock:
            return self._is_listening

    def set_lifecycle_handlers(
        self,
        *,
        listening_changed: Callable[[bool], None],
        unexpected_exit: Callable[[str], None],
    ) -> None:
        self._listening_changed = listening_changed
        self._unexpected_exit = unexpected_exit
        with self.server_lock:
            if self._active_generation is not None:
                self._active_generation.listening_changed = listening_changed
                self._active_generation.unexpected_exit = unexpected_exit

    def _set_listening(
        self, value: bool, generation: _ServerGeneration | None = None
    ) -> None:
        with self.server_lock:
            if generation is not None and generation is not self._active_generation:
                return
            if self._is_listening == value:
                return
            self._is_listening = value
            handler = generation.listening_changed if generation else self._listening_changed
        handler(value)

    async def list_resources(self) -> list[Resource]:
        return [
            Resource(
                uri="metrics://all",
                name="All Metrics",
                description="Prometheus metrics in text format",
                mimeType="text/plain",
            )
        ]

    async def _scrape_metrics_text(self) -> str:
        self._registry.track_mcp_request_received("read_resource:metrics")
        try:
            data = generate_latest(self._registry.registry).decode("utf-8")
            self._registry.track_mcp_response_sent("read_resource:metrics", "success")
            return data
        except Exception:
            self._registry.track_mcp_response_sent("read_resource:metrics", "error")
            raise

    async def _mcp_read_resource(self, uri) -> str:
        uri_str = str(uri)
        if uri_str != "metrics://all":
            raise ValueError(f"Resource {uri_str} not found")
        return await self._scrape_metrics_text()

    async def read_resource(self, uri: str) -> list[TextResourceContents]:
        uri_str = str(uri)
        if uri_str != "metrics://all":
            raise ValueError(f"Resource {uri_str} not found")
        data = await self._scrape_metrics_text()
        return [TextResourceContents(uri=uri_str, mimeType="text/plain", text=data)]

    def _create_sse_app(self) -> Starlette:
        """Legacy HTTP+SSE transport (same layout as MCPServerImpl)."""
        return build_legacy_sse_app(self.mcp_server)

    def _create_app(self) -> Starlette:
        prometheus_app = make_asgi_app(registry=self._registry.registry)
        mcp_route, lifespan = build_streamable_http_route(self.mcp_server)

        return Starlette(
            routes=[
                Mount("/metrics", app=prometheus_app),
                mcp_route,
                Mount(MCP_LEGACY_SSE_MOUNT_PATH, app=self._create_sse_app()),
            ],
            lifespan=lifespan,
        )

    def start_server(self, host: str, port: int) -> None:
        """Start the metrics server (Prometheus + MCP)."""
        with self.server_lock:
            has_generation = self._active_generation is not None
        if has_generation:
            self.stop_server()

        with self.server_lock:
            self._current_host = host
            self._current_port = port
            self._generation_number += 1
            generation = _ServerGeneration(
                number=self._generation_number,
                host=host,
                port=port,
                stop_event=threading.Event(),
                start_failed_handler=self._start_failed_handler,
                listening_changed=self._listening_changed,
                unexpected_exit=self._unexpected_exit,
            )
            self._active_generation = generation
            self._stop_event = generation.stop_event
            self._startup_notified = False
            self._is_listening = False

            thread = threading.Thread(
                target=self._run_uvicorn, args=(generation,), daemon=True
            )
            generation.thread = thread
            self.thread = thread
            thread.start()
            logger.info("Metrics server starting on %s:%d", host, port)
            if not is_localhost_bind_host(host):
                logger.warning(
                    "metrics_server_non_localhost_bind host=%s port=%d — "
                    "metrics and MCP resources are exposed without authentication",
                    host,
                    port,
                )

    def _notify_started(self, generation: _ServerGeneration | None = None) -> None:
        if generation is None:
            if self._startup_notified or self._stop_event.is_set():
                return
            self._startup_notified = True
            host, port = self._current_host, self._current_port
        else:
            with generation.callback_lock:
                with self.server_lock:
                    if (
                        generation is not self._active_generation
                        or not generation.callbacks_open
                        or generation.startup_notified
                        or generation.stop_event.is_set()
                    ):
                        return
                    generation.startup_notified = True
                    self._startup_notified = True
                    changed = not self._is_listening
                    self._is_listening = True
                    host, port = generation.host, generation.port
                    handler = generation.listening_changed
                if changed:
                    handler(True)
                logger.info(
                    "metrics_server_listening host=%s port=%d", host, port
                )
                return
        self._set_listening(True)
        logger.info("metrics_server_listening host=%s port=%d", host, port)

    def _notify_start_failed(
        self, message: str, generation: _ServerGeneration | None = None
    ) -> None:
        if generation is not None:
            with generation.callback_lock:
                with self.server_lock:
                    if (
                        generation is not self._active_generation
                        or not generation.callbacks_open
                        or generation.stop_event.is_set()
                    ):
                        return
                    host, port = generation.host, generation.port
                    handler = generation.start_failed_handler
                    if handler is None:
                        self._pending_start_failure = message
                logger.error(
                    "metrics_server_start_failed host=%s port=%d message=%s",
                    host,
                    port,
                    message,
                )
                if handler is not None:
                    handler(message)
                return
        else:
            host, port = self._current_host, self._current_port
            handler = self._start_failed_handler
        logger.error(
            "metrics_server_start_failed host=%s port=%d message=%s",
            host,
            port,
            message,
        )
        if handler is None:
            self._pending_start_failure = message
            return
        handler(message)

    def _run_uvicorn(self, generation: _ServerGeneration | None = None) -> None:
        managed = generation is not None
        if generation is None:
            generation = _ServerGeneration(
                0,
                self._current_host,
                self._current_port,
                self._stop_event,
                startup_notified=self._startup_notified,
                start_failed_handler=self._start_failed_handler,
                listening_changed=self._listening_changed,
                unexpected_exit=self._unexpected_exit,
            )
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        def thread_exit(code=0):
            if code != 0:
                raise OSError(
                    errno.EADDRINUSE,
                    f"bind failed on {generation.host}:{generation.port}",
                )
            original = get_process_exit_original() or sys.exit
            return original(code)

        _install_thread_exit(thread_exit)

        try:
            app = self._create_app()
            config = uvicorn.Config(
                app=app,
                host=generation.host,
                port=generation.port,
                loop="asyncio",
                log_config=None,
                log_level="warning",
            )
            server_instance = uvicorn.Server(config)
            generation.server_instance = server_instance
            with self.server_lock:
                if not managed or generation is self._active_generation:
                    self.server_instance = server_instance
            setattr(server_instance, "install_signal_handlers", lambda: None)

            original_startup = server_instance.startup

            async def startup_with_notify(sockets=None):
                await original_startup(sockets=sockets)
                self._notify_started(generation if managed else None)

            setattr(server_instance, "startup", startup_with_notify)

            loop.run_until_complete(server_instance.serve())
        except OSError as exc:
            self._notify_start_failed(
                format_bind_error(
                    exc, generation.host, generation.port, "metrics server"
                ),
                generation if managed else None,
            )
        except Exception as exc:
            logger.exception("metrics_server_start_failed")
            self._notify_start_failed(
                f"Metrics server failed to start: {exc}",
                generation if managed else None,
            )
        finally:
            _uninstall_thread_exit()
            drain_pending_tasks(loop)
            loop.close()
            if managed:
                self._finalize_generation(generation)
            else:
                self._set_listening(False)
                if not generation.stop_event.is_set() and generation.startup_notified:
                    logger.warning("metrics_server_unexpected_exit")
                    generation.unexpected_exit("listener_stopped")

    def _finalize_generation(self, generation: _ServerGeneration) -> None:
        with generation.callback_lock:
            with self.server_lock:
                active = (
                    generation is self._active_generation
                    and generation.callbacks_open
                    and not generation.stop_event.is_set()
                )
                if active:
                    generation.callbacks_open = False
                    changed = self._is_listening
                    self._is_listening = False
                    listening_handler = generation.listening_changed
                    unexpected = generation.startup_notified
                    unexpected_handler = generation.unexpected_exit
                else:
                    changed = False
                    unexpected = False
            if changed:
                listening_handler(False)
            if unexpected:
                logger.warning("metrics_server_unexpected_exit")
                unexpected_handler("listener_stopped")

    def stop_server(self) -> None:
        """Stop the metrics server."""
        with self.server_lock:
            generation = self._active_generation
            thread = generation.thread if generation is not None else self.thread
            server_instance = (
                generation.server_instance
                if generation is not None
                else self.server_instance
            )
            if generation is None:
                self._stop_event.set()
        if generation is not None:
            with generation.callback_lock:
                with self.server_lock:
                    if generation is self._active_generation:
                        generation.callbacks_open = False
                        generation.stop_event.set()
                        changed = self._is_listening
                        self._is_listening = False
                        listening_handler = generation.listening_changed
                    else:
                        changed = False
                    if server_instance:
                        server_instance.should_exit = True
                if changed:
                    listening_handler(False)
        elif server_instance:
            server_instance.should_exit = True
        if thread and thread is not threading.current_thread():
            thread.join(timeout=2.0)
        if generation is None:
            self._set_listening(False)
        with self.server_lock:
            if generation is self._active_generation:
                self.thread = None
                self.server_instance = None
                self._active_generation = None
                logger.info("Metrics server stopped")

    def restart_server(self, host: str, port: int) -> None:
        """Restart the metrics server with new settings."""
        self.stop_server()
        self.start_server(host, port)
