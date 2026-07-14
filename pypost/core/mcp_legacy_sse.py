"""Legacy HTTP+SSE MCP transport (Starlette sub-app).

Module-level ASGI endpoints support isolated unit tests and reuse by
``MCPServerImpl`` and ``MetricsServer``.

Routing efficiency (PYPOST-159): the outer app mounts this module via ``Mount`` (no
``request_response`` wrapper). ``MessagesEndpoint`` is a direct ASGI callable on ``Route``;
only GET ``/`` uses ``handle_sse_get`` (``request_response``) to return an empty ``Response``
after ``connect_sse`` completes. See ``doc/dev/mcp_integration.md``.
"""
from __future__ import annotations

from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from pypost.core.mcp_transport_routes import MCP_LEGACY_SSE_MESSAGES_PATH


class SSEEndpoint:
    """ASGI callable for the legacy SSE stream (GET /)."""

    def __init__(self, server: Server, sse_transport: SseServerTransport) -> None:
        self.server = server
        self.sse_transport = sse_transport

    async def __call__(self, scope, receive, send):
        async with self.sse_transport.connect_sse(scope, receive, send) as streams:
            opts = self.server.create_initialization_options()
            await self.server.run(streams[0], streams[1], opts)


class MessagesEndpoint:
    """ASGI callable for legacy client POST messages."""

    def __init__(self, sse_transport: SseServerTransport) -> None:
        self.sse_transport = sse_transport

    async def __call__(self, scope, receive, send):
        await self.sse_transport.handle_post_message(scope, receive, send)


def build_legacy_sse_app(
    server: Server,
    messages_path: str = MCP_LEGACY_SSE_MESSAGES_PATH,
    *,
    debug: bool = False,
) -> Starlette:
    """Build the inner Starlette app mounted at ``MCP_LEGACY_SSE_MOUNT_PATH``."""
    sse = SseServerTransport(messages_path)

    async def handle_sse_get(request: Request) -> Response:
        ep = SSEEndpoint(server, sse)
        await ep(request.scope, request.receive, request._send)
        return Response()

    return Starlette(
        debug=debug,
        routes=[
            Route(
                messages_path,
                endpoint=MessagesEndpoint(sse),
                methods=["POST"],
            ),
            Route("/", endpoint=handle_sse_get, methods=["GET"]),
        ],
    )
