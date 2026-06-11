"""Shared harness for CollectionTreeActions unit tests in isolation."""

from __future__ import annotations

from dataclasses import dataclass, field
from unittest.mock import MagicMock

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QTreeView

from pypost.models.models import Collection, RequestData
from pypost.ui.presenters.collection_tree_actions import CollectionTreeActions


def make_collection(col_id: str, name: str, requests=None) -> Collection:
    return Collection(id=col_id, name=name, requests=requests or [])


def make_request(req_id: str, name: str, method: str = "GET") -> RequestData:
    return RequestData(id=req_id, name=name, method=method)


class FakeRequestManager:
    def __init__(self, collections=None):
        self.collections = collections or []
        self.storage = MagicMock()
        self.storage.load_collections.return_value = self.collections

    def reload_collections(self):
        self.collections = self.storage.load_collections()

    def get_collections(self):
        return self.collections

    def delete_collection_item(self, item_id, item_type):
        if item_type == "request":
            for col in self.collections:
                col.requests = [req for req in col.requests if req.id != item_id]
        elif item_type == "collection":
            self.collections = [col for col in self.collections if col.id != item_id]
        return True

    def rename_collection_item(self, item_id, item_type, new_name):
        if item_type == "collection":
            for col in self.collections:
                if col.id == item_id:
                    col.name = new_name
                    return True
        elif item_type == "request":
            for col in self.collections:
                for req in col.requests:
                    if req.id == item_id:
                        req.name = new_name
                        return True
        return True


@dataclass
class IsolatedTreeActions:
    actions: CollectionTreeActions
    view: QTreeView
    model: QStandardItemModel
    request_manager: FakeRequestManager
    metrics: MagicMock
    emit_collections_changed: MagicMock = field(default_factory=MagicMock)
    emit_request_renamed: MagicMock = field(default_factory=MagicMock)
    emit_requests_deleted: MagicMock = field(default_factory=MagicMock)
    emit_open_isolated_tab: MagicMock = field(default_factory=MagicMock)
    refresh_tree: MagicMock = field(default_factory=MagicMock)
    restore_tree_state: MagicMock = field(default_factory=MagicMock)
    _collection_items_by_id: dict[str, QStandardItem] = field(default_factory=dict)

    def find_item(self, item_id: str, item_type: str) -> QStandardItem | None:
        if item_type == "collection":
            return self._collection_items_by_id.get(item_id)
        for row in range(self.model.rowCount()):
            col_item = self.model.item(row)
            for child_row in range(col_item.rowCount()):
                req_item = col_item.child(child_row)
                data = req_item.data(Qt.UserRole)
                if item_type == "request" and isinstance(data, RequestData) and data.id == item_id:
                    return req_item
        return None

    def remove_item(self, item_id: str, item_type: str) -> bool:
        item = self.find_item(item_id, item_type)
        if item is None:
            return False
        parent = item.parent() or self.model.invisibleRootItem()
        parent.removeRow(item.row())
        if item_type == "collection":
            self._collection_items_by_id.pop(item_id, None)
        return True

    def load_collections(self, collections=None) -> None:
        if collections is not None:
            self.request_manager.collections = collections
        self.model.clear()
        self._collection_items_by_id.clear()
        for col in self.request_manager.get_collections():
            col_item = QStandardItem(col.name)
            col_item.setData(col.id, Qt.UserRole)
            col_item.setEditable(False)
            for req in col.requests:
                req_item = QStandardItem(f"{req.method} {req.name}")
                req_item.setData(req, Qt.UserRole)
                req_item.setEditable(False)
                col_item.appendRow(req_item)
            self.model.appendRow(col_item)
            self._collection_items_by_id[col.id] = col_item


def build_isolated_tree_actions(collections=None) -> IsolatedTreeActions:
    harness = IsolatedTreeActions(
        actions=None,  # type: ignore[arg-type]
        view=QTreeView(),
        model=QStandardItemModel(),
        request_manager=FakeRequestManager(collections or []),
        metrics=MagicMock(),
    )
    harness.view.setModel(harness.model)
    harness.actions = CollectionTreeActions(
        harness.view,
        harness.model,
        harness.request_manager,
        harness.metrics,
        find_item=harness.find_item,
        remove_item=harness.remove_item,
        refresh_tree=harness.refresh_tree,
        restore_tree_state=harness.restore_tree_state,
        emit_collections_changed=harness.emit_collections_changed,
        emit_request_renamed=harness.emit_request_renamed,
        emit_requests_deleted=harness.emit_requests_deleted,
        emit_open_isolated_tab=harness.emit_open_isolated_tab,
    )
    if collections:
        harness.load_collections()
    return harness
