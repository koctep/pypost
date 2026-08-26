"""Tab dirty-state helpers (UI layer)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pypost.core.request_persisted_fields import persisted_fields_equal
from pypost.core.websocket_persisted_fields import (
    factory_websocket_draft,
    persisted_websocket_fields_equal,
    websocket_draft_fields_equal,
)
from pypost.models.websocket import WebSocketConnection

if TYPE_CHECKING:
    from pypost.ui.presenters.tabs_presenter import RequestTab
    from pypost.ui.widgets.websocket.websocket_tab import WebSocketTab


def is_tab_dirty(tab: RequestTab) -> bool:
    """Return True when the tab editor differs from its adopted persisted baseline."""
    baseline = tab.persisted_baseline
    if baseline is None:
        return False
    ui_data = tab.request_editor.get_request_data_from_ui()
    return not persisted_fields_equal(ui_data, baseline)


def connection_snapshot_from_tab(tab: WebSocketTab) -> WebSocketConnection:
    """Editor-visible persisted fields at save time (FR-1.3).

    Handshake and MCP chrome come from the connection editor; presets and
    sequences prefer the live ``presenter.connection`` (composer mutations).
    """
    editor = tab.connection_editor
    source = tab.connection_data
    live = getattr(tab.presenter, "connection", None) or source
    raw_sub = editor.subprotocols_input.text()
    subprotocols = [part.strip() for part in raw_sub.split(",") if part.strip()]
    return WebSocketConnection(
        id=source.id,
        name=source.name,
        url=editor.url_input.text(),
        params=editor.params_table.get_data(),
        headers=editor.headers_table.get_data(),
        subprotocols=subprotocols,
        expose_as_mcp=editor.mcp_expose_check.isChecked(),
        mcp_description=editor.mcp_description_edit.text(),
        mcp_params=getattr(live, "mcp_params", source.mcp_params),
        mcp_probe_preset_id=getattr(
            live, "mcp_probe_preset_id", source.mcp_probe_preset_id
        ),
        mcp_probe_max_messages=getattr(
            live, "mcp_probe_max_messages", source.mcp_probe_max_messages
        ),
        mcp_probe_max_duration_ms=getattr(
            live, "mcp_probe_max_duration_ms", source.mcp_probe_max_duration_ms
        ),
        presets=list(getattr(live, "presets", source.presets) or []),
        sequences=list(getattr(live, "sequences", source.sequences) or []),
    )


def is_websocket_draft_dirty(tab: WebSocketTab) -> bool:
    """True when editor-visible fields differ from new-profile factory defaults."""
    current = connection_snapshot_from_tab(tab)
    return not websocket_draft_fields_equal(current, factory_websocket_draft())


def is_websocket_saved_tab_dirty(tab: WebSocketTab) -> bool:
    """True when a saved-profile tab differs from its adopted persisted baseline."""
    baseline = tab.persisted_baseline
    if baseline is None:
        return False
    current = connection_snapshot_from_tab(tab)
    return not persisted_websocket_fields_equal(current, baseline)
