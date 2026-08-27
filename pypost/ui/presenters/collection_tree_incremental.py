"""Incremental collection tree refresh when disk structure is unchanged."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem

from pypost.models.mcp_client import McpClientConnection
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


def _child_items(col: Collection) -> list[tuple[object, str]]:
    items: list[tuple[object, str]] = []
    for req in col.requests:
        items.append((req, "request"))
    for ws in getattr(col, "websockets", []):
        items.append((ws, "websocket"))
    for profile in getattr(col, "mcp_clients", []):
        items.append((profile, "mcp_client"))
    return items


def _item_id(data: object) -> str | None:
    if isinstance(data, RequestData):
        return data.id
    if isinstance(data, WebSocketConnection):
        return data.id
    if isinstance(data, McpClientConnection):
        return data.id
    return None


def _item_label(data: object, item_type: str) -> str:
    if isinstance(data, RequestData):
        return f"{data.method} {data.name}"
    if isinstance(data, WebSocketConnection):
        return f"ws {data.name}"
    if isinstance(data, McpClientConnection):
        return f"mcp {data.name}"
    return item_type


def try_incremental_tree_refresh(
    collection_items_by_id: dict[str, QStandardItem],
    collections: list[Collection],
) -> bool:
    """Update existing tree nodes in place when collection/item ids are unchanged."""
    if {col.id for col in collections} != set(collection_items_by_id):
        return False

    for col in collections:
        col_item = collection_items_by_id.get(col.id)
        expected = _child_items(col)
        if col_item is None or col_item.rowCount() != len(expected):
            return False
        for row, (item_data, item_type) in enumerate(expected):
            data = col_item.child(row).data(Qt.ItemDataRole.UserRole)
            item_id = _item_id(item_data)
            if item_id is None or _item_id(data) != item_id:
                return False
            if item_type == "request" and not isinstance(data, RequestData):
                return False
            if item_type == "websocket" and not isinstance(data, WebSocketConnection):
                return False
            if item_type == "mcp_client" and not isinstance(data, McpClientConnection):
                return False

    for col in collections:
        col_item = collection_items_by_id[col.id]
        col_item.setText(col.name)
        for row, (item_data, item_type) in enumerate(_child_items(col)):
            child = col_item.child(row)
            child.setText(_item_label(item_data, item_type))
            child.setData(item_data, Qt.ItemDataRole.UserRole)

    return True
