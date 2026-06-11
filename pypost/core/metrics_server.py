"""Metrics HTTP/MCP server lifecycle (uvicorn thread)."""

import asyncio
import errno
import logging
import sys
import threading
from collections.abc import Callable

import uvicorn
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import Resource, TextResourceContents
from prometheus_client import generate_latest, make_asgi_app
from starlette.applications import Starlette
from starlette.routing import Mount

from pypost.core.mcp_streamable_http import build_streamable_http_route
from pypost.core.mcp_transport_routes import (
    MCP_LEGACY_SSE_MESSAGES_PATH,
    MCP_LEGACY_SSE_MOUNT_PATH,
)
from pypost.core.metrics_registry import MetricsRegistry
from pypost.core.server_bind import format_bind_error

logger = logging.getLogger(__name__)


class MetricsServer:
    """Owns observability MCP resources and uvicorn server lifecycle."""

    def __init__(self, registry: MetricsRegistry) -> None:
        self._registry = registry
        self.server_instance = None
        self.thread = None
        self.server_lock = threading.Lock()
        self._current_host = "127.0.0.1"
        self._current_port = 9080
        self._stop_event = threading.Event()
        self._startup_notified = False
        self._start_failed_handler: Callable[[str], None] | None = None
        self._pending_start_failure: str | None = None

        self.mcp_server = Server("pypost-metrics")
        self.mcp_server.list_resources()(self.list_resources)
        self.mcp_server.read_resource()(self.read_resource)

    def set_start_failed_handler(
        self, handler: Callable[[str], None] | None
    ) -> None:
        """Register a callback for bind/startup failures (may run off main thread)."""
        self._start_failed_handler = handler
        pending = self._pending_start_failure
        if pending is not None and handler is not None:
            self._pending_start_failure = None
            handler(pending)

    async def list_resources(self) -> list[Resource]:
        return [
            Resource(
                uri="metrics://all",
                name="All Metrics",
                description="Prometheus metrics in text format",
                mimeType="text/plain",
            )
        ]

    async def read_resource(self, uri: str) -> list[TextResourceContents]:
        if uri == "metrics://all":
            self._registry.track_mcp_request_received("read_resource:metrics")
            try:
                data = generate_latest(self._registry.registry).decode("utf-8")
                self._registry.track_mcp_response_sent("read_resource:metrics", "success")
                return [TextResourceContents(uri=uri, mimeType="text/plain", text=data)]
            except Exception:
                self._registry.track_mcp_response_sent("read_resource:metrics", "error")
                raise

        raise ValueError(f"Resource {uri} not found")

    def _create_app(self) -> Starlette:
        prometheus_app = make_asgi_app(registry=self._registry.registry)
        mcp_route, lifespan = build_streamable_http_route(self.mcp_server)

        sse = SseServerTransport(MCP_LEGACY_SSE_MESSAGES_PATH)

        class SSEEndpoint:
            def __init__(self, server, sse_transport):
                self.server = server
                self.sse_transport = sse_transport

            async def __call__(self, scope, receive, send):
                async with self.sse_transport.connect_sse(scope, receive, send) as streams:
                    init_opts = self.server.create_initialization_options()
                    await self.server.run(streams[0], streams[1], init_opts)

        class MessagesEndpoint:
            def __init__(self, sse_transport):
                self.sse_transport = sse_transport

            async def __call__(self, scope, receive, send):
                if scope["type"] == "http" and scope["method"] != "POST":
                    await self._send_response(send, 405, b"Method Not Allowed")
                    return
                await self.sse_transport.handle_post_message(scope, receive, send)

            async def _send_response(self, send, status, body):
                await send(
                    {
                        "type": "http.response.start",
                        "status": status,
                        "headers": [(b"content-type", b"text/plain")],
                    }
                )
                await send(
                    {
                        "type": "http.response.body",
                        "body": body,
                    }
                )

        return Starlette(
            routes=[
                Mount("/metrics", app=prometheus_app),
                mcp_route,
                Mount(MCP_LEGACY_SSE_MOUNT_PATH, app=SSEEndpoint(self.mcp_server, sse)),
                Mount(MCP_LEGACY_SSE_MESSAGES_PATH, app=MessagesEndpoint(sse)),
            ],
            lifespan=lifespan,
        )

    def start_server(self, host: str, port: int) -> None:
        """Start the metrics server (Prometheus + MCP)."""
        with self.server_lock:
            if self.thread and self.thread.is_alive():
                self.stop_server()

            self._current_host = host
            self._current_port = port
            self._stop_event.clear()
            self._startup_notified = False

            self.thread = threading.Thread(target=self._run_uvicorn, daemon=True)
            self.thread.start()
            logger.info("Metrics server starting on %s:%d", host, port)

    def _notify_started(self) -> None:
        if self._startup_notified or self._stop_event.is_set():
            return
        self._startup_notified = True
        logger.info(
            "metrics_server_listening host=%s port=%d",
            self._current_host,
            self._current_port,
        )

    def _notify_start_failed(self, message: str) -> None:
        logger.error(
            "metrics_server_start_failed host=%s port=%d message=%s",
            self._current_host,
            self._current_port,
            message,
        )
        handler = self._start_failed_handler
        if handler is None:
            self._pending_start_failure = message
            return
        handler(message)

    def _run_uvicorn(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        original_exit = sys.exit

        def thread_exit(code=0):
            if code != 0:
                raise OSError(
                    errno.EADDRINUSE,
                    f"bind failed on {self._current_host}:{self._current_port}",
                )
            original_exit(code)

        sys.exit = thread_exit
        try:
            app = self._create_app()
            config = uvicorn.Config(
                app=app,
                host=self._current_host,
                port=self._current_port,
                loop="asyncio",
                log_level="warning",
            )
            self.server_instance = uvicorn.Server(config)
            self.server_instance.install_signal_handlers = lambda: None

            original_startup = self.server_instance.startup

            async def startup_with_notify(sockets=None):
                await original_startup(sockets=sockets)
                self._notify_started()

            self.server_instance.startup = startup_with_notify

            loop.run_until_complete(self.server_instance.serve())
        except OSError as exc:
            self._notify_start_failed(
                format_bind_error(
                    exc, self._current_host, self._current_port, "metrics server"
                )
            )
        except Exception as exc:
            logger.exception("metrics_server_start_failed")
            self._notify_start_failed(f"Metrics server failed to start: {exc}")
        finally:
            sys.exit = original_exit
            loop.close()
            if not self._stop_event.is_set() and self._startup_notified:
                logger.warning("metrics_server_unexpected_exit")

    def stop_server(self) -> None:
        """Stop the metrics server."""
        with self.server_lock:
            self._stop_event.set()
            if self.server_instance:
                self.server_instance.should_exit = True

            if self.thread:
                self.thread.join(timeout=2.0)
                self.thread = None
                self.server_instance = None
                logger.info("Metrics server stopped")

    def restart_server(self, host: str, port: int) -> None:
        """Restart the metrics server with new settings."""
        self.stop_server()
        self.start_server(host, port)
