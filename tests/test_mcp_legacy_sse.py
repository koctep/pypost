"""Tests for module-level legacy SSE MCP endpoints."""

import inspect
import unittest
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch

import anyio
import pytest
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.testclient import TestClient

from pypost.core.mcp_legacy_sse import (
    MessagesEndpoint,
    SSEEndpoint,
    build_legacy_sse_app,
)
from pypost.core.mcp_transport_routes import (
    MCP_LEGACY_SSE_MESSAGES_PATH,
    MCP_LEGACY_SSE_MOUNT_PATH,
)

pytestmark = pytest.mark.timeout(60)


@asynccontextmanager
async def _quick_connect_sse(self, scope, receive, send):
    """Minimal connect_sse stand-in so GET / completes without a live SSE stream."""
    read_writer, read_stream = anyio.create_memory_object_stream(0)
    write_stream, write_reader = anyio.create_memory_object_stream(0)
    try:
        yield (read_stream, write_stream)
    finally:
        await read_writer.aclose()
        await write_reader.aclose()


def _legacy_sse_test_client(*, mounted: bool = False) -> TestClient:
    app = build_legacy_sse_app(Server("test"))
    if mounted:
        app = Starlette(routes=[Mount(MCP_LEGACY_SSE_MOUNT_PATH, app=app)])
    return TestClient(app, raise_server_exceptions=False)


class TestMcpLegacySseModule(unittest.TestCase):
    def test_endpoints_are_importable_at_module_level(self):
        self.assertTrue(callable(SSEEndpoint))
        self.assertTrue(callable(MessagesEndpoint))

    def test_messages_endpoint_does_not_format_responses_manually(self):
        source = inspect.getsource(MessagesEndpoint)
        self.assertNotIn("_send_response", source)
        self.assertNotIn("http.response.start", source)
        self.assertNotIn("starlette.responses", source)

    def test_build_legacy_sse_app_exposes_post_messages_and_get_root(self):
        app = build_legacy_sse_app(Server("test"))
        inner_paths = []
        for route in app.routes:
            if isinstance(route, Route):
                inner_paths.append((route.path, route.methods))
        post_messages = [
            p
            for p in inner_paths
            if p[0] == MCP_LEGACY_SSE_MESSAGES_PATH and "POST" in p[1]
        ]
        self.assertEqual(len(post_messages), 1)
        get_roots = [p for p in inner_paths if "GET" in p[1] and p[0] == "/"]
        self.assertEqual(len(get_roots), 1)


class TestMcpLegacySseHttpGuards(unittest.TestCase):
    def test_sse_get_returns_empty_response_after_connection_closes(self):
        """handle_sse_get must return Response() after transport teardown (MCP SDK contract)."""
        client = TestClient(build_legacy_sse_app(Server("test")), raise_server_exceptions=True)
        with patch.object(SseServerTransport, "connect_sse", _quick_connect_sse):
            with patch.object(Server, "run", new_callable=AsyncMock) as mock_run:
                response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "")
        self.assertTrue(mock_run.called)

    def test_inner_app_rejects_non_get_on_sse_stream(self):
        client = _legacy_sse_test_client()
        for method in ("post", "put", "delete", "patch"):
            with self.subTest(method=method):
                self.assertEqual(getattr(client, method)("/").status_code, 405)

    def test_inner_app_rejects_non_post_on_messages(self):
        client = _legacy_sse_test_client()
        for method in ("get", "put", "delete", "patch"):
            with self.subTest(method=method):
                self.assertEqual(
                    getattr(client, method)(MCP_LEGACY_SSE_MESSAGES_PATH).status_code,
                    405,
                )

    def test_mounted_sse_app_rejects_wrong_methods(self):
        client = _legacy_sse_test_client(mounted=True)
        self.assertEqual(client.post(MCP_LEGACY_SSE_MOUNT_PATH).status_code, 405)
        self.assertEqual(
            client.get(
                f"{MCP_LEGACY_SSE_MOUNT_PATH}{MCP_LEGACY_SSE_MESSAGES_PATH}"
            ).status_code,
            405,
        )


if __name__ == "__main__":
    unittest.main()
