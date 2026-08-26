"""In-memory outbound MCP Client draft (peer of WebSocketConnection).

Not persisted on Collection in PYPOST-1166. MCP-TM-7 adds save/open.
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
