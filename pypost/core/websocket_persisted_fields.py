"""Qt-free helpers for WebSocket tab isolation and dirty detection.

Draft dirty detection compares editor-visible handshake, MCP, preset, and
sequence fields against a new unsaved profile's factory defaults. Saved-profile
dirty detection compares the same fields against a ``persisted_baseline`` snapshot
(set when opening collection-backed tabs). Ephemeral ``id`` is ignored for draft
comparisons — drafts have no disk baseline until PYPOST-1161 save.
"""

from __future__ import annotations

from pypost.models.websocket import WebSocketConnection

_FACTORY_DRAFT_ID = "websocket-factory-draft"

_PERSISTED_FIELD_NAMES = (
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


def copy_websocket_for_isolated_tab(data: WebSocketConnection) -> WebSocketConnection:
    """Return a deep copy of *data* for isolated tab ownership."""
    return data.model_copy(deep=True)


def snapshot_websocket_persisted_fields(data: WebSocketConnection) -> WebSocketConnection:
    """Return a deep copy used as the persisted-field baseline for a tab."""
    return copy_websocket_for_isolated_tab(data)


def persisted_websocket_fields_equal(
    a: WebSocketConnection, b: WebSocketConnection
) -> bool:
    """Return True when two connections match on all persisted editor fields."""
    for field_name in _PERSISTED_FIELD_NAMES:
        if getattr(a, field_name) != getattr(b, field_name):
            return False
    return True


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
