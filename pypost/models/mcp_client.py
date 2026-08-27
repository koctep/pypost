"""Outbound MCP Client profile model (peer of WebSocketConnection).

Saved profiles live on ``Collection.mcp_clients`` (PYPOST-1172).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

__all__ = ["McpClientConnection", "McpClientSessionState", "McpRemoteTool"]


@dataclass(frozen=True)
class McpRemoteTool:
    """Discovered remote tool kept in presenter memory (not persisted)."""

    name: str
    description: str = ""
    input_schema: dict[str, Any] | None = None


class McpClientSessionState(str, Enum):
    """Outbound discovery chrome: failed Connect uses FAILED, not CONNECTED."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    FAILED = "failed"


class McpClientConnection(BaseModel):
    """Unsaved outbound MCP Client draft identity, URL, and headers."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New MCP Client"
    url: str = ""
    headers: dict[str, str] = Field(default_factory=dict)
    last_tool_name: str | None = None
    last_tool_arguments: dict[str, Any] = Field(default_factory=dict)
