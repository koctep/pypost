"""Central MCP HTTP transport path configuration.

All MCP server Starlette mounts and SseServerTransport paths should import from here
so route changes require a single edit.
"""
from __future__ import annotations

MCP_STREAMABLE_HTTP_PATH = "/mcp"
MCP_LEGACY_SSE_MOUNT_PATH = "/sse"
MCP_LEGACY_SSE_MESSAGES_PATH = "/messages"
