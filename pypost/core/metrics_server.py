"""Metrics HTTP/MCP server lifecycle (uvicorn thread)."""

import asyncio
import logging
import threading

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

logger = logging.getLogger(__name__)


class MetricsServer:
    """Owns observability MCP resources and uvicorn server lifecycle."""

    def __init__(self, registry: MetricsRegistry) -> None:
        self._registry = registry
        self.server_instance = None
        self.thread = None
        self.server_lock = threading.Lock()

        self.mcp_server = Server("pypost-metrics")
        self.mcp_server.list_resources()(self.list_resources)
        self.mcp_server.read_resource()(self.read_resource)

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

            self.thread = threading.Thread(target=self._run_uvicorn, daemon=True)
            self.thread.start()
            logger.info("Metrics server started on %s:%d", host, port)

    def _run_uvicorn(self) -> None:
        app = self._create_app()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        config = uvicorn.Config(
            app=app,
            host=self._current_host,
            port=self._current_port,
            loop="asyncio",
            log_level="warning",
        )
        self.server_instance = uvicorn.Server(config)
        self.server_instance.install_signal_handlers = lambda: None

        loop.run_until_complete(self.server_instance.serve())

    def stop_server(self) -> None:
        """Stop the metrics server."""
        with self.server_lock:
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
