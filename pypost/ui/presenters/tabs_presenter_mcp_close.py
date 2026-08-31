"""MCP Client profile tab close helper (PYPOST-1172)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pypost.models.mcp_client import McpClientSessionState
from pypost.ui.collection_item_dialogs import (
    TabClosePromptProtocol,
    prompt_deleted_websocket_profile_tab_close,
)
from pypost.ui.presenters.tab_dirty import is_mcp_client_saved_tab_dirty
from pypost.ui.widgets.mcp_client import McpClientTab

if TYPE_CHECKING:
    from pypost.ui.presenters.tabs_presenter import TabsPresenter

logger = logging.getLogger(__name__)

_ACTIVE_MCP_SESSION_STATES = (
    McpClientSessionState.CONNECTING,
    McpClientSessionState.CONNECTED,
)


def rename_mcp_client_tabs(
    presenter: TabsPresenter,
    profile_id: str,
    new_name: str,
) -> None:
    """Updates tab labels after an MCP Client profile rename."""
    for i in range(presenter._tabs.count()):
        tab = presenter._tabs.widget(i)
        if (
            isinstance(tab, McpClientTab)
            and tab.connection_data
            and tab.connection_data.id == profile_id
        ):
            tab.connection_data.name = new_name
            presenter._header.set_tab_label(i, new_name)
            if tab.persisted_baseline is not None:
                tab.persisted_baseline.name = new_name


def close_tabs_for_mcp_client_ids(
    presenter: TabsPresenter,
    profile_ids: list[str],
    *,
    prompt: TabClosePromptProtocol | None = None,
) -> None:
    """Closes tabs bound to deleted MCP Client profile ids; prompts when at risk."""
    if not profile_ids:
        return
    ids_to_close = set(profile_ids)
    prompt_fn = prompt if prompt is not None else prompt_deleted_websocket_profile_tab_close
    indices_to_close: list[int] = []
    for i in range(presenter._tabs.count()):
        tab = presenter._tabs.widget(i)
        if not isinstance(tab, McpClientTab):
            continue
        conn = tab.connection_data
        if conn is None or conn.id not in ids_to_close:
            continue
        has_unsaved = is_mcp_client_saved_tab_dirty(tab)
        has_active = tab.presenter.state in _ACTIVE_MCP_SESSION_STATES
        if has_unsaved or has_active:
            title = conn.name if conn.name else "MCP Client"
            if not prompt_fn(
                presenter._tabs,
                title,
                has_unsaved_edits=has_unsaved,
                has_active_connection=has_active,
            ):
                continue
        indices_to_close.append(i)
    for index in reversed(indices_to_close):
        presenter._tabs.removeTab(index)
    if presenter._request_tab_count() == 0:
        presenter.add_new_tab(save_state=False)
    elif indices_to_close:
        preferred = max(0, min(indices_to_close) - 1)
        presenter._ensure_current_is_navigable(preferred)
    presenter.save_tabs_state()
    logger.info(
        "close_tabs_for_deleted_mcp_clients closed_count=%d profile_ids=%s",
        len(indices_to_close),
        sorted(ids_to_close),
    )
