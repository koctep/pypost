"""Tests for module-level legacy SSE MCP endpoints."""

import pytest

pytestmark = pytest.mark.timeout(60)

import unittest

from mcp.server import Server
from starlette.routing import Route
from starlette.testclient import TestClient

from pypost.core.mcp_legacy_sse import (
    MessagesEndpoint,
    SSEEndpoint,
    build_legacy_sse_app,
)
from pypost.core.mcp_transport_routes import MCP_LEGACY_SSE_MESSAGES_PATH


class TestMcpLegacySseModule(unittest.TestCase):
    def test_endpoints_are_importable_at_module_level(self):
        self.assertTrue(callable(SSEEndpoint))
        self.assertTrue(callable(MessagesEndpoint))

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

    def test_build_legacy_sse_app_rejects_wrong_http_methods(self):
        client = TestClient(
            build_legacy_sse_app(Server("test")),
            raise_server_exceptions=False,
        )
        self.assertEqual(
            client.get(MCP_LEGACY_SSE_MESSAGES_PATH).status_code,
            405,
        )
        self.assertEqual(client.post("/").status_code, 405)


if __name__ == "__main__":
    unittest.main()
