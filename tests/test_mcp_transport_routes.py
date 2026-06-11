"""Tests for centralized MCP transport route constants."""
import pytest

pytestmark = pytest.mark.timeout(30)


def test_mcp_transport_route_constants_are_absolute_paths():
    from pypost.core.mcp_transport_routes import (
        MCP_LEGACY_SSE_MESSAGES_PATH,
        MCP_LEGACY_SSE_MOUNT_PATH,
        MCP_STREAMABLE_HTTP_PATH,
    )

    assert MCP_STREAMABLE_HTTP_PATH == "/mcp"
    assert MCP_LEGACY_SSE_MOUNT_PATH == "/sse"
    assert MCP_LEGACY_SSE_MESSAGES_PATH == "/messages"
    for path in (
        MCP_STREAMABLE_HTTP_PATH,
        MCP_LEGACY_SSE_MOUNT_PATH,
        MCP_LEGACY_SSE_MESSAGES_PATH,
    ):
        assert path.startswith("/")
        assert " " not in path
