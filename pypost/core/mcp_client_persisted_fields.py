"""Qt-free helpers for MCP Client tab isolation and dirty detection."""

from __future__ import annotations

from pypost.models.mcp_client import McpClientConnection

_FACTORY_DRAFT_ID = "mcp-client-factory-draft"

_PERSISTED_FIELD_NAMES = (
    "name",
    "url",
    "headers",
    "last_tool_name",
    "last_tool_arguments",
)

_DRAFT_FIELD_NAMES = _PERSISTED_FIELD_NAMES


def copy_mcp_client_for_isolated_tab(data: McpClientConnection) -> McpClientConnection:
    """Return a deep copy of *data* for isolated tab ownership."""
    return data.model_copy(deep=True)


def snapshot_mcp_client_persisted_fields(data: McpClientConnection) -> McpClientConnection:
    """Return a deep copy used as the persisted-field baseline for a tab."""
    return copy_mcp_client_for_isolated_tab(data)


def persisted_mcp_client_fields_equal(
    a: McpClientConnection, b: McpClientConnection
) -> bool:
    """Return True when two profiles match on all persisted editor fields."""
    for field_name in _PERSISTED_FIELD_NAMES:
        if getattr(a, field_name) != getattr(b, field_name):
            return False
    return True


def factory_mcp_client_draft() -> McpClientConnection:
    """Return ``McpClientConnection()`` with a stable dummy id for comparisons."""
    return McpClientConnection(id=_FACTORY_DRAFT_ID)


def mcp_client_draft_fields_equal(
    a: McpClientConnection, b: McpClientConnection
) -> bool:
    """Return True when two profiles match on draft-visible editor fields."""
    for field_name in _DRAFT_FIELD_NAMES:
        if getattr(a, field_name) != getattr(b, field_name):
            return False
    return True
