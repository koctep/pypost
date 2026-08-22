"""Incremental collection tree refresh when disk structure is unchanged."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem

from pypost.models.models import Collection, RequestData
from pypost.models.websocket import WebSocketConnection


def log_tree_refresh(collection_count: int, request_count: int, *, incremental: bool) -> None:
    import logging

    logger = logging.getLogger(__name__)
    event = "refresh_tree_incremental" if incremental else "refresh_tree_completed"
    logger.info(
        "%s collection_count=%d request_count=%d",
        event,
        collection_count,
        request_count,
    )


def try_incremental_tree_refresh(
    collection_items_by_id: dict[str, QStandardItem],
    collections: list[Collection],
) -> bool:
    """Update existing tree nodes in place when collection/request ids are unchanged."""
    if {col.id for col in collections} != set(collection_items_by_id):
        return False

    for col in collections:
        col_item = collection_items_by_id.get(col.id)
        ws_list = getattr(col, "websockets", [])
        expected_count = len(col.requests) + len(ws_list)
        if col_item is None or col_item.rowCount() != expected_count:
            return False
        for row, req in enumerate(col.requests):
            data = col_item.child(row).data(Qt.ItemDataRole.UserRole)
            if not isinstance(data, RequestData) or data.id != req.id:
                return False
        offset = len(col.requests)
        for row, ws in enumerate(ws_list):
            data = col_item.child(offset + row).data(Qt.ItemDataRole.UserRole)
            if not isinstance(data, WebSocketConnection) or data.id != ws.id:
                return False

    for col in collections:
        col_item = collection_items_by_id[col.id]
        col_item.setText(col.name)
        for row, req in enumerate(col.requests):
            req_item = col_item.child(row)
            req_item.setText(f"{req.method} {req.name}")
            req_item.setData(req, Qt.ItemDataRole.UserRole)
        offset = len(col.requests)
        for row, ws in enumerate(getattr(col, "websockets", [])):
            ws_item = col_item.child(offset + row)
            ws_item.setText(f"ws {ws.name}")
            ws_item.setData(ws, Qt.ItemDataRole.UserRole)

    return True
