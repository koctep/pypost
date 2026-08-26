"""Draft persist and close helpers extracted from TabsPresenter (PYPOST-1158)."""

from __future__ import annotations

import logging
from collections.abc import Callable

from PySide6.QtWidgets import QTabWidget, QWidget

from pypost.core.request_manager import RequestManager
from pypost.core.websocket_registry import WebSocketRegistry
from pypost.ui.collection_item_dialogs import prompt_unsaved_draft_tab_close
from pypost.ui.presenters.tab_dirty import is_websocket_draft_dirty
from pypost.ui.widgets.websocket.websocket_tab import WebSocketTab

logger = logging.getLogger(__name__)

PromptClose = Callable[[QWidget, str], bool]


def websocket_id_is_saved(request_manager: RequestManager, ws_id: str) -> bool:
    """Return True when *ws_id* resolves to a collection-backed WebSocket profile."""
    storage = getattr(request_manager, "storage", None)
    registry = WebSocketRegistry(request_manager, storage)
    return registry.find_websocket(ws_id) is not None


def collect_persistable_open_tab_ids(
    tabs: QTabWidget,
    *,
    websocket_id_is_saved: Callable[[str], bool],
) -> list[str]:
    """Collect HTTP ids and saved WebSocket ids; omit MCP Client and WS drafts."""
    open_ids: list[str] = []
    omitted_draft_count = 0
    persisted_ws_count = 0
    for i in range(tabs.count()):
        tab = tabs.widget(i)
        if isinstance(tab, WebSocketTab):
            conn = tab.connection_data
            if conn and conn.id and websocket_id_is_saved(conn.id):
                open_ids.append(conn.id)
                persisted_ws_count += 1
                logger.info(
                    "websocket_saved_tab_persisted_in_open_tabs connection_id=%s",
                    conn.id,
                )
            elif conn and conn.id:
                omitted_draft_count += 1
                logger.info(
                    "websocket_draft_omitted_from_open_tabs connection_id=%s",
                    conn.id,
                )
            continue
        request_data = getattr(tab, "request_data", None)
        req_id = getattr(request_data, "id", None)
        if req_id:
            open_ids.append(req_id)
    if omitted_draft_count or persisted_ws_count:
        logger.info(
            "websocket_open_tabs_filter omitted_draft_count=%d persisted_ws_count=%d",
            omitted_draft_count,
            persisted_ws_count,
        )
    return open_ids


def confirm_close_websocket_draft(
    parent: QWidget,
    tab: object,
    *,
    websocket_id_is_saved: Callable[[str], bool],
    prompt_close: PromptClose | None = None,
) -> bool:
    """Return True if close_tab should proceed (not dirty, saved, or user discarded)."""
    if not isinstance(tab, WebSocketTab):
        return True
    conn = tab.connection_data
    if conn is None:
        return True
    if websocket_id_is_saved(conn.id):
        return True
    if not is_websocket_draft_dirty(tab):
        logger.info(
            "websocket_draft_clean_close connection_id=%s",
            conn.id,
        )
        return True
    closer = prompt_close if prompt_close is not None else prompt_unsaved_draft_tab_close
    title = conn.name if conn.name else "New WebSocket"
    discarded = closer(parent, title)
    logger.info(
        "websocket_draft_dirty_close_prompt connection_id=%s choice=%s",
        conn.id,
        "discard" if discarded else "keep",
    )
    return discarded
