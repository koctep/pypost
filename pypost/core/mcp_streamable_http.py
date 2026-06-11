"""Shared Streamable HTTP transport setup for PyPost MCP servers."""

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

from mcp.server import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.routing import Route
from starlette.types import Receive, Scope, Send

MCP_STREAMABLE_HTTP_PATH = "/mcp"


class StreamableHTTPASGIApp:
    """ASGI endpoint delegating to StreamableHTTPSessionManager."""

    def __init__(self, session_manager: StreamableHTTPSessionManager) -> None:
        self._session_manager = session_manager

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        await self._session_manager.handle_request(scope, receive, send)


def build_streamable_http_route(
    server: Server,
) -> tuple[Route, Callable]:
    """Build the /mcp route and Starlette lifespan for the given MCP Server."""
    session_manager = StreamableHTTPSessionManager(app=server)
    route = Route(
        MCP_STREAMABLE_HTTP_PATH,
        endpoint=StreamableHTTPASGIApp(session_manager),
    )

    @asynccontextmanager
    async def lifespan(_app) -> AsyncIterator[None]:
        async with session_manager.run():
            yield

    return route, lifespan
