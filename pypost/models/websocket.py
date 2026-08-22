from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Dict, List, Optional
import uuid

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from pypost.models.models import McpToolParam


class WsMessageFormat(str, Enum):
    TEXT = "text"
    JSON = "json"
    HEX = "hex"
    BASE64 = "base64"


class HeartbeatPolicy(BaseModel):
    enabled: bool = True
    interval_seconds: int = Field(default=30, ge=5, le=3600)
    timeout_seconds: int = Field(default=10, ge=1, le=300)


class ReconnectPolicy(BaseModel):
    enabled: bool = True
    max_attempts: int = Field(default=5, ge=0, le=100)
    initial_delay_seconds: float = Field(default=1.0, gt=0)
    backoff_multiplier: float = Field(default=2.0, ge=1.0)
    max_delay_seconds: float = Field(default=30.0, gt=0)


class WebSocketMessagePreset(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Message"
    format: WsMessageFormat = WsMessageFormat.JSON
    payload: str = ""  # template text; never a resolved value


class WebSocketSequenceStep(BaseModel):
    preset_id: Optional[str] = None
    inline_payload: str = ""
    format: WsMessageFormat = WsMessageFormat.JSON
    delay_ms: int = Field(default=0, ge=0, le=600_000)  # waited BEFORE this step


class WebSocketSequence(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New Sequence"
    steps: List[WebSocketSequenceStep] = Field(default_factory=list)


class WebSocketConnection(BaseModel):
    """Saved, reusable description of a real-time endpoint. Peer of RequestData."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "New WebSocket"
    url: str = ""  # ws:// or wss://, may contain {{ vars }}
    headers: Dict[str, str] = Field(default_factory=dict)
    params: Dict[str, str] = Field(default_factory=dict)
    subprotocols: List[str] = Field(default_factory=list)
    heartbeat: HeartbeatPolicy = Field(default_factory=HeartbeatPolicy)
    reconnect: ReconnectPolicy = Field(default_factory=ReconnectPolicy)
    presets: List[WebSocketMessagePreset] = Field(default_factory=list)
    sequences: List[WebSocketSequence] = Field(default_factory=list)
    default_format: WsMessageFormat = WsMessageFormat.JSON

    # MCP tool configuration fields (authoritatively owned by WS-2)
    expose_as_mcp: bool = False
    mcp_description: str = ""
    mcp_params: Dict[str, McpToolParam] = Field(default_factory=dict)
    mcp_probe_preset_id: Optional[str] = None
    mcp_probe_max_messages: Optional[int] = None
    mcp_probe_max_duration_ms: Optional[int] = None


try:
    from pypost.models.models import McpToolParam as _McpToolParam
    WebSocketConnection.model_rebuild(_types_namespace={"McpToolParam": _McpToolParam})
except (ImportError, AttributeError):
    pass
