"""ASGI compatibility tests for MCP and metrics Starlette apps (PYPOST-161)."""

import unittest
from unittest.mock import patch

import pytest
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from prometheus_client import make_asgi_app
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.testclient import TestClient

from pypost.core.mcp_legacy_sse import (
    MessagesEndpoint,
    build_legacy_sse_app,
)
from pypost.core.mcp_server_impl import MCPServerImpl
from pypost.core.mcp_streamable_http import StreamableHTTPASGIApp
from pypost.core.mcp_transport_routes import (
    MCP_LEGACY_SSE_MESSAGES_PATH,
    MCP_LEGACY_SSE_MOUNT_PATH,
    MCP_STREAMABLE_HTTP_PATH,
)
from pypost.core.metrics_registry import MetricsRegistry
from pypost.core.metrics_server import MetricsServer

pytestmark = pytest.mark.timeout(30)


def _assert_route_uses_direct_asgi(route: Route, expected_type: type) -> None:
    """Starlette must register the endpoint as ASGI, not request_response."""
    assert isinstance(route, Route)
    assert isinstance(route.app, expected_type), (
        f"Expected direct ASGI {expected_type.__name__}, got {type(route.app).__name__}. "
        "request_response wrapping would cause TypeError on None response."
    )


def _find_route(app: Starlette, path: str) -> Route | None:
    for route in app.routes:
        if isinstance(route, Route) and route.path == path:
            return route
    return None


def _find_mount(app: Starlette, path: str) -> Mount | None:
    for route in app.routes:
        if isinstance(route, Mount) and route.path == path:
            return route
    return None


class TestLegacySseAsgiCompatibility(unittest.TestCase):
    def test_messages_endpoint_route_is_direct_asgi(self):
        app = build_legacy_sse_app(Server("test"))
        route = _find_route(app, MCP_LEGACY_SSE_MESSAGES_PATH)
        self.assertIsNotNone(route)
        _assert_route_uses_direct_asgi(route, MessagesEndpoint)

    def test_messages_post_invokes_asgi_without_type_error(self):
        app = build_legacy_sse_app(Server("test"))
        client = TestClient(app, raise_server_exceptions=True)

        async def _fake_handle_post_message(scope, receive, send):
            await send(
                {"type": "http.response.start", "status": 202, "headers": []}
            )
            await send(
                {"type": "http.response.body", "body": b"", "more_body": False}
            )

        with patch.object(
            SseServerTransport,
            "handle_post_message",
            side_effect=_fake_handle_post_message,
        ) as mock_post:
            response = client.post(MCP_LEGACY_SSE_MESSAGES_PATH, json={})
        self.assertEqual(response.status_code, 202)
        self.assertTrue(mock_post.called)


class TestStreamableHttpAsgiCompatibility(unittest.TestCase):
    def test_mcp_server_streamable_http_route_is_direct_asgi(self):
        app = MCPServerImpl().create_app()
        route = _find_route(app, MCP_STREAMABLE_HTTP_PATH)
        self.assertIsNotNone(route)
        _assert_route_uses_direct_asgi(route, StreamableHTTPASGIApp)

    def test_metrics_server_streamable_http_route_is_direct_asgi(self):
        app = MetricsServer(MetricsRegistry())._create_app()
        route = _find_route(app, MCP_STREAMABLE_HTTP_PATH)
        self.assertIsNotNone(route)
        _assert_route_uses_direct_asgi(route, StreamableHTTPASGIApp)


class TestMetricsServerAsgiCompatibility(unittest.TestCase):
    def test_create_app_exposes_metrics_mount_streamable_http_and_sse(self):
        app = MetricsServer(MetricsRegistry())._create_app()
        metrics_mount = _find_mount(app, "/metrics")
        sse_mount = _find_mount(app, MCP_LEGACY_SSE_MOUNT_PATH)
        mcp_route = _find_route(app, MCP_STREAMABLE_HTTP_PATH)
        self.assertIsNotNone(metrics_mount)
        self.assertIsNotNone(sse_mount)
        self.assertIsNotNone(mcp_route)
        self.assertIsInstance(sse_mount.app, Starlette)

    def test_metrics_mount_serves_prometheus_via_asgi(self):
        registry = MetricsRegistry()
        registry.track_gui_send_click()
        server = MetricsServer(registry)
        mount = _find_mount(server._create_app(), "/metrics")
        self.assertIsNotNone(mount)
        self.assertTrue(callable(mount.app))
        expected = make_asgi_app(registry=registry.registry)
        self.assertEqual(type(mount.app), type(expected))

        client = TestClient(server._create_app(), raise_server_exceptions=False)
        response = client.get("/metrics")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/plain", response.headers.get("content-type", ""))
        self.assertIn("gui_send_clicks_total 1.0", response.text)

    def test_metrics_app_sse_mount_reuses_legacy_asgi_subapp(self):
        app = MetricsServer(MetricsRegistry())._create_app()
        sse_mount = _find_mount(app, MCP_LEGACY_SSE_MOUNT_PATH)
        route = _find_route(sse_mount.app, MCP_LEGACY_SSE_MESSAGES_PATH)
        self.assertIsNotNone(route)
        _assert_route_uses_direct_asgi(route, MessagesEndpoint)


class TestMcpServerAsgiCompatibility(unittest.TestCase):
    def test_create_app_exposes_streamable_http_and_sse_mount(self):
        app = MCPServerImpl().create_app()
        self.assertIsNotNone(_find_route(app, MCP_STREAMABLE_HTTP_PATH))
        sse_mount = _find_mount(app, MCP_LEGACY_SSE_MOUNT_PATH)
        self.assertIsNotNone(sse_mount)
        self.assertIsInstance(sse_mount.app, Starlette)

    def test_inner_sse_messages_route_is_direct_asgi(self):
        app = MCPServerImpl().create_app()
        sse_mount = _find_mount(app, MCP_LEGACY_SSE_MOUNT_PATH)
        route = _find_route(sse_mount.app, MCP_LEGACY_SSE_MESSAGES_PATH)
        self.assertIsNotNone(route)
        _assert_route_uses_direct_asgi(route, MessagesEndpoint)


if __name__ == "__main__":
    unittest.main()
