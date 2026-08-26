"""Shared fixtures for collections tree and CollectionTreeActions tests."""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Iterator
from unittest.mock import MagicMock, patch

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QAbstractItemDelegate, QApplication, QLineEdit, QTreeView

from pypost.models.models import Collection, RequestData
from pypost.models.websocket import WebSocketConnection
from pypost.ui.delegates.collection_item_rename_delegate import CollectionItemRenameDelegate
from pypost.ui.presenters.collection_tree_actions import CollectionTreeActions
from tests.helpers.qt_item_view import detach_item_view_model

_QMENU_PATCH = "pypost.ui.presenters.collection_tree_actions.QMenu"


def make_collection(
    col_id: str,
    name: str,
    requests=None,
    *,
    websockets=None,
) -> Collection:
    return Collection(
        id=col_id,
        name=name,
        requests=requests or [],
        websockets=websockets or [],
    )


def make_websocket(ws_id: str, name: str, **kwargs) -> WebSocketConnection:
    return WebSocketConnection(id=ws_id, name=name, **kwargs)


def make_request(req_id: str, name: str, method: str = "GET") -> RequestData:
    return RequestData(id=req_id, name=name, method=method)


class FakeRequestManager:
    def __init__(self, collections=None):
        self.collections = collections or []
        self.deleted = []
        self.renamed = []
        self.storage = MagicMock()
        self.storage.load_collections.return_value = self.collections

    def reload_collections(self):
        self.collections = self.storage.load_collections()

    def apply_loaded_collections(self, collections):
        self.collections = list(collections)

    def get_collections(self):
        return self.collections

    def delete_collection_item(self, item_id, item_type):
        self.deleted.append((item_id, item_type))
        if item_type == "request":
            for col in self.collections:
                col.requests = [req for req in col.requests if req.id != item_id]
        elif item_type == "websocket":
            for col in self.collections:
                col.websockets = [ws for ws in col.websockets if ws.id != item_id]
        elif item_type == "collection":
            self.collections = [col for col in self.collections if col.id != item_id]
        return True

    def rename_collection_item(self, item_id, item_type, new_name):
        self.renamed.append((item_id, item_type, new_name))
        normalized = new_name.strip()
        if not normalized:
            return False
        if item_type == "request":
            for col in self.collections:
                for req in col.requests:
                    if req.id == item_id:
                        req.name = normalized
                        return True
        elif item_type == "collection":
            for col in self.collections:
                if col.id == item_id:
                    col.name = normalized
                    return True
        elif item_type == "websocket":
            for col in self.collections:
                for ws in col.websockets:
                    if ws.id == item_id:
                        ws.name = normalized
                        return True
        return False


class FakeStateManager:
    def __init__(self):
        self._expanded = []

    def get_expanded_collections(self):
        return list(self._expanded)

    def set_expanded_collections(self, ids):
        self._expanded = ids


class FakeMetrics:
    def track_gui_collection_delete_action(self, *args):
        pass

    def track_gui_collection_rename_action(self, *args):
        pass


@contextmanager
def patch_tree_context_menu(actions, selected) -> Iterator[MagicMock]:
    """Patch CollectionTreeActions QMenu; yield the mock menu instance."""
    with patch(_QMENU_PATCH) as mock_menu_class:
        mock_menu = MagicMock()
        mock_menu.addAction.side_effect = list(actions)
        mock_menu.exec.return_value = selected
        mock_menu_class.return_value = mock_menu
        yield mock_menu


@contextmanager
def patch_view_context_menu(view, item_index, actions, selected) -> Iterator[MagicMock]:
    """Patch view.indexAt and CollectionTreeActions QMenu."""
    with patch.object(view, "indexAt", return_value=item_index):
        with patch_tree_context_menu(actions, selected) as mock_menu:
            yield mock_menu


def make_delete_menu_actions(action_count: int) -> tuple[list[MagicMock], MagicMock]:
    """Build mocked menu actions for delete flows.

    ``action_count`` is the full menu size after PYPOST-1013:
    - 3: collection row [Export, Rename, Delete]
    - 4: request row [New tab, Export, Rename, Delete]
    """
    export_action = MagicMock()
    rename_action = MagicMock()
    delete_action = MagicMock()
    if action_count == 3:
        return [export_action, rename_action, delete_action], delete_action
    new_tab_action = MagicMock()
    return [new_tab_action, export_action, rename_action, delete_action], delete_action


@contextmanager
def patch_delete_context_menu(view, item_index, *, action_count: int = 3) -> Iterator[MagicMock]:
    """Patch view and QMenu for delete-selected context-menu flows."""
    actions, delete_action = make_delete_menu_actions(action_count)
    with patch_view_context_menu(view, item_index, actions, delete_action):
        yield delete_action


@contextmanager
def patch_rename_context_menu(view, item_index, *, action_count: int = 3) -> Iterator[MagicMock]:
    """Patch view and QMenu for rename-selected context-menu flows.

    ``action_count`` is the full menu size after PYPOST-1013:
    - 3: collection row [Export, Rename, Delete]
    - 4: request row [New tab, Export, Rename, Delete]
    """
    export_action = MagicMock()
    rename_action = MagicMock()
    delete_action = MagicMock()
    if action_count == 3:
        actions = [export_action, rename_action, delete_action]
    else:
        new_tab_action = MagicMock()
        actions = [new_tab_action, export_action, rename_action, delete_action]
    with patch_view_context_menu(view, item_index, actions, rename_action):
        yield rename_action


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
    emit_open_isolated_websocket_tab: MagicMock = field(default_factory=MagicMock)
    emit_websockets_deleted: MagicMock = field(default_factory=MagicMock)
    export_collection: MagicMock = field(default_factory=MagicMock)
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
                if (
                    item_type == "websocket"
                    and isinstance(data, WebSocketConnection)
                    and data.id == item_id
                ):
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
            for ws in col.websockets:
                ws_item = QStandardItem(f"ws {ws.name}")
                ws_item.setData(ws, Qt.UserRole)
                ws_item.setEditable(False)
                col_item.appendRow(ws_item)
            self.model.appendRow(col_item)
            self._collection_items_by_id[col.id] = col_item


def wire_rename_delegate(harness: IsolatedTreeActions) -> None:
    """Install CollectionItemRenameDelegate wired to tree actions (production parity)."""
    harness.view.setItemDelegate(
        CollectionItemRenameDelegate(
            is_rename_index=harness.actions.is_rename_index,
            on_committed=harness.actions.handle_rename_committed,
            on_cancelled=harness.actions.handle_rename_cancelled,
            on_rejected_empty=harness.actions.handle_rename_rejected_empty,
            parent=harness.view,
        )
    )


def wait_for_rename_editor(view: QTreeView, *, timeout_ms: int = 2000) -> QLineEdit:
    """Poll until the inline rename QLineEdit appears after QTreeView.edit."""
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        QApplication.processEvents()
        editors = [editor for editor in view.findChildren(QLineEdit) if editor.isVisible()]
        if editors:
            return editors[-1]
    raise AssertionError("Rename editor did not appear")


def commit_inline_rename(view: QTreeView, editor: QLineEdit, new_name: str) -> None:
    """Commit rename text through the view delegate (simulates Enter)."""
    editor.setText(new_name)
    view.commitData(editor)
    QApplication.processEvents()


def cancel_inline_rename(
    view: QTreeView,
    editor: QLineEdit,
) -> None:
    """Cancel inline rename via delegate closeEditor (simulates Escape)."""
    delegate = view.itemDelegate()
    delegate.closeEditor.emit(editor, QAbstractItemDelegate.EndEditHint.RevertModelCache)
    QApplication.processEvents()


def build_isolated_tree_actions(
    collections=None,
    *,
    with_rename_delegate: bool = False,
) -> IsolatedTreeActions:
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
        export_collection=harness.export_collection,
    )
    if with_rename_delegate:
        wire_rename_delegate(harness)
    if collections:
        harness.load_collections()
    return harness


def close_isolated_tree_actions(harness: IsolatedTreeActions) -> None:
    """Detach the model via shared qt_item_view helper, then close the view."""
    detach_item_view_model(harness.view)
    harness.view.close()
    QApplication.processEvents()


@contextmanager
def isolated_tree_actions(
    collections=None,
    *,
    with_rename_delegate: bool = False,
) -> Iterator[IsolatedTreeActions]:
    """Build an isolated tree harness and tear it down with shared detach."""
    harness = build_isolated_tree_actions(
        collections,
        with_rename_delegate=with_rename_delegate,
    )
    try:
        yield harness
    finally:
        close_isolated_tree_actions(harness)
