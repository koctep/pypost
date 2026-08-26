"""In-memory outbound MCP Client draft (peer of WebSocketConnection).

Not persisted on Collection in PYPOST-1166. MCP-TM-7 adds save/open.
"""

from __future__ import annotations

import uuid
from enum import Enum

from pydantic import BaseModel, Field

__all__ = ["McpClientConnection", "McpClientSessionState"]


class McpClientSessionState(str, Enum):
    """Local chrome session state (live initialize is MCP-TM-3)."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"


class McpClientConnection(BaseModel):
    """Unsaved outbound MCP Client draft identity and URL."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New MCP Client"
    url: str = ""
