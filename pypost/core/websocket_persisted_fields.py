"""Qt-free comparison helpers for unsaved WebSocket draft editor fields.

Draft dirty detection compares editor-visible handshake, MCP, preset, and
sequence fields against a new unsaved profile's factory defaults. Ephemeral
``id`` is ignored — drafts have no disk baseline until PYPOST-1161 save.
"""

from __future__ import annotations

from pypost.models.websocket import WebSocketConnection

_FACTORY_DRAFT_ID = "websocket-factory-draft"

_DRAFT_FIELD_NAMES = (
    "name",
    "url",
    "headers",
    "params",
    "subprotocols",
    "presets",
    "sequences",
    "expose_as_mcp",
    "mcp_description",
    "mcp_params",
    "mcp_probe_preset_id",
    "mcp_probe_max_messages",
    "mcp_probe_max_duration_ms",
)


def factory_websocket_draft() -> WebSocketConnection:
    """Return ``WebSocketConnection()`` with a stable dummy id for comparisons."""
    return WebSocketConnection(id=_FACTORY_DRAFT_ID)


def websocket_draft_fields_equal(
    a: WebSocketConnection, b: WebSocketConnection
) -> bool:
    """Return True when two connections match on draft-visible editor fields."""
    for field_name in _DRAFT_FIELD_NAMES:
        if getattr(a, field_name) != getattr(b, field_name):
            return False
    return True
