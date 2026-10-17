"""Shared Streamable HTTP transport setup for PyPost MCP servers."""
from __future__ import annotations

import json
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

from mcp.server import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.responses import Response
from starlette.routing import Route
from starlette.types import Message, Receive, Scope, Send

from pypost.core.mcp_transport_routes import MCP_STREAMABLE_HTTP_PATH


class StreamableHTTPASGIApp:
    """ASGI endpoint delegating to StreamableHTTPSessionManager.

    Validates UTF-8 encoding of incoming JSON-RPC payloads before delegating
    to the underlying session manager, returning a JSON-RPC Parse Error (-32700)
    with HTTP 400 if character decoding fails.
    """

    def __init__(self, session_manager: StreamableHTTPSessionManager) -> None:
        self._session_manager = session_manager

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope.get("method") != "POST":
            await self._session_manager.handle_request(scope, receive, send)
            return

        body_chunks: list[bytes] = []
        more_body = True
        while more_body:
            message = await receive()
            if message["type"] == "http.request":
                body_chunks.append(message.get("body", b""))
                more_body = message.get("more_body", False)
            else:
                body_chunks.append(b"")
                break

        full_body = b"".join(body_chunks)
        try:
            full_body.decode("utf-8")
        except UnicodeDecodeError as exc:
            payload = json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": "server-error",
                    "error": {
                        "code": -32700,
                        "message": f"Parse error: {exc}",
                    },
                }
            ).encode("utf-8")
            response = Response(
                content=payload,
                status_code=400,
                media_type="application/json",
            )
            await response(scope, receive, send)
            return

        idx = 0

        async def replay_receive() -> Message:
            nonlocal idx
            if idx < len(body_chunks):
                chunk = body_chunks[idx]
                idx += 1
                return {
                    "type": "http.request",
                    "body": chunk,
                    "more_body": idx < len(body_chunks),
                }
            return await receive()

        await self._session_manager.handle_request(scope, replay_receive, send)


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
