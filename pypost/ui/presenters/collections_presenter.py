from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QModelIndex, QObject, Qt, Signal
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QTreeView, QWidget

from pypost.core.collection_export import build_export_payload
from pypost.core.collection_import import load_collection_import_candidates
from pypost.core.metrics_protocol import MetricsTrackerProtocol
from pypost.core.request_persisted_fields import copy_request_for_isolated_tab
from pypost.core.request_manager import RequestManager
from pypost.core.qt.state_manager import StateManager
from pypost.models.models import Collection, RequestData
from pypost.ui.delegates import CollectionItemRenameDelegate
from pypost.ui.presenters.collection_export_actions import CollectionExportActions
from pypost.ui.presenters.collection_import_actions import CollectionImportActions
from pypost.ui.presenters.collection_tree_actions import CollectionTreeActions
from pypost.ui.presenters.collection_tree_incremental import (
    log_tree_refresh,
    try_incremental_tree_refresh,
)
from pypost.ui.presenters.collections_async_loader import CollectionsAsyncLoader
from pypost.ui.presenters.collections_panel import build_collections_panel
from pypost.ui.widget_ids import COLLECTION_TREE, set_widget_id

logger = logging.getLogger(__name__)


class CollectionsPresenter(QObject):
    """Owns the collections tree view: loading, rendering, rename, delete, and tab opening."""

    open_request_in_tab = Signal(object)  # payload: RequestData (deep copy for new tab)
    open_request_in_isolated_tab = Signal(object)  # payload: RequestData (deep copy)
    collections_changed = Signal()  # after create / delete / rename
    collections_loaded = Signal()  # after async startup load completes
    request_renamed = Signal(str, str)  # (request_id, new_name)
    requests_deleted = Signal(list)  # request IDs whose tabs should close

    def __init__(
        self,
        request_manager: RequestManager,
        state_manager: StateManager,
        metrics: MetricsTrackerProtocol,
        icons: dict,
        storage=None,
        parent: QObject | None = None,
        *,
        read_import_file: (
            Callable[[Path], tuple[list[Collection], list[str]]] | None
        ) = None,
        serialize_collection: Callable[[Collection], dict] | None = build_export_payload,
    ) -> None:
        super().__init__(parent)
        self._request_manager = request_manager
        self._state_manager = state_manager
        self._metrics = metrics
        self._icons = icons
        self._read_import_file = read_import_file or load_collection_import_candidates
        self._async_loader = (
            CollectionsAsyncLoader(
                request_manager,
                storage,
                self.refresh_tree,
                parent=self,
            )
            if storage is not None
            else None
        )
        if self._async_loader is not None:
            self._async_loader.collections_loaded.connect(self.collections_loaded.emit)

        self._collection_items_by_id: dict[str, QStandardItem] = {}
        self._view = QTreeView()
        # Parented to the view so the model outlives it: once the view is held
        # by the panel's layout, C++ owns the view while Python owns the model,
        # and an unparented model can be freed first during teardown.
        self._model = QStandardItemModel(self._view)
        set_widget_id(self._view, COLLECTION_TREE)
        self._view.setHeaderHidden(True)
        self._view.setModel(self._model)
        self._view.clicked.connect(self._on_collection_clicked)
        self._view.setContextMenuPolicy(Qt.CustomContextMenu)
        self._view.expanded.connect(self._on_tree_expanded)
        self._view.collapsed.connect(self._on_tree_collapsed)

        self._tree_actions = CollectionTreeActions(
            self._view,
            self._model,
            self._request_manager,
            self._metrics,
            find_item=self._find_collection_item,
            remove_item=self.remove_item_from_tree,
            refresh_tree=self.refresh_tree,
            restore_tree_state=self.restore_tree_state,
            emit_collections_changed=self.collections_changed.emit,
            emit_request_renamed=self.request_renamed.emit,
            emit_requests_deleted=self.requests_deleted.emit,
            emit_open_isolated_tab=self.open_request_in_isolated_tab.emit,
            export_collection=self._export_collection_at_index,
        )
        self._view.setItemDelegate(
            CollectionItemRenameDelegate(
                is_rename_index=self._tree_actions.is_rename_index,
                on_committed=self._tree_actions.handle_rename_committed,
                on_cancelled=self._tree_actions.handle_rename_cancelled,
                on_rejected_empty=self._tree_actions.handle_rename_rejected_empty,
                parent=self._view,
            )
        )
        self._view.customContextMenuRequested.connect(self._tree_actions.show_context_menu)
        self._panel = build_collections_panel(
            self._view,
            import_collection=self.import_collections,
            export_collection=self.export_collection,
        )
        self._import_actions = CollectionImportActions(
            self._panel,
            self._request_manager,
            read_import_file=self._read_import_file,
            refresh_tree=self.refresh_tree,
            restore_tree_state=self.restore_tree_state,
            emit_collections_changed=self.collections_changed.emit,
            show_status=self._show_import_status,
            clear_status=self._clear_import_status,
            parent=self,
        )
        self._export_actions = CollectionExportActions(
            self._panel,
            self._view,
            self._model,
            self._request_manager,
            serialize_collection=serialize_collection,
        )

    @property
    def widget(self) -> QTreeView:
        return self._view

    @property
    def panel(self) -> QWidget:
        """Sidebar container: the collections tree plus its action row."""
        return self._panel

    def collection_by_id(self, collection_id: str) -> Collection | None:
        """Resolve a persisted collection ID from the in-memory collection cache."""
        return next(
            (
                collection
                for collection in self._request_manager.get_collections()
                if collection.id == collection_id
            ),
            None,
        )

    @property
    def _pending_rename(self) -> dict | None:
        return self._tree_actions.pending_rename

    @_pending_rename.setter
    def _pending_rename(self, value: dict | None) -> None:
        self._tree_actions._pending_rename = value

    def _make_collection_item(self, col: Collection) -> QStandardItem:
        col_item = QStandardItem(col.name)
        col_item.setData(col.id, Qt.UserRole)
        col_item.setEditable(False)
        if "collection" in self._icons:
            col_item.setIcon(self._icons["collection"])
        return col_item

    def _make_request_item(self, req: RequestData) -> QStandardItem:
        req_item = QStandardItem(f"{req.method} {req.name}")
        req_item.setData(req, Qt.UserRole)
        req_item.setEditable(False)
        if req.method in self._icons:
            req_item.setIcon(self._icons[req.method])
        return req_item

    def _expand_collection_if_saved(self, collection_id: str, col_item: QStandardItem) -> None:
        if collection_id in self._state_manager.get_expanded_collections():
            self._view.setExpanded(col_item.index(), True)

    def refresh_tree(self) -> None:
        """Rebuilds tree model from RequestManager in-memory collections."""
        collections = self._request_manager.get_collections()
        req_count = sum(len(col.requests) for col in collections)
        if try_incremental_tree_refresh(self._collection_items_by_id, collections):
            log_tree_refresh(len(collections), req_count, incremental=True)
            return
        self._model.clear()
        self._collection_items_by_id.clear()
        for col in collections:
            col_item = self._make_collection_item(col)
            for req in col.requests:
                col_item.appendRow(self._make_request_item(req))
            self._model.appendRow(col_item)
            self._collection_items_by_id[col.id] = col_item
        log_tree_refresh(len(collections), req_count, incremental=False)

    def add_saved_request_to_tree(self, request: RequestData, collection_id: str) -> bool:
        """Insert a newly saved request without rebuilding the full tree model."""
        col_item = self._find_collection_item(collection_id, "collection")
        if col_item is None:
            for col in self._request_manager.get_collections():
                if col.id == collection_id:
                    return self._insert_collection_into_tree(col)
            logger.warning(
                "add_saved_request_to_tree_failed reason=collection_not_found"
                " collection_id=%s request_id=%s",
                collection_id,
                request.id,
            )
            return False

        col_item.appendRow(self._make_request_item(request))
        self._expand_collection_if_saved(collection_id, col_item)
        logger.info(
            "add_saved_request_to_tree_completed collection_id=%s request_id=%s",
            collection_id,
            request.id,
        )
        return True

    def _insert_collection_into_tree(self, collection: Collection) -> bool:
        if self._find_collection_item(collection.id, "collection") is not None:
            return False
        col_item = self._make_collection_item(collection)
        for req in collection.requests:
            col_item.appendRow(self._make_request_item(req))
        self._model.appendRow(col_item)
        self._collection_items_by_id[collection.id] = col_item
        self._expand_collection_if_saved(collection.id, col_item)
        logger.info(
            "insert_collection_into_tree_completed collection_id=%s request_count=%d",
            collection.id,
            len(collection.requests),
        )
        return True

    def load_collections(self) -> None:
        """Reloads collections from storage and rebuilds the tree model."""
        if self._async_loader is not None:
            self._async_loader.try_load_async()
            return
        self._request_manager.reload_collections()
        self.refresh_tree()

    def load_collections_async(self) -> None:
        """Loads collections from storage on a background thread (startup path)."""
        if self._async_loader is None:
            logger.warning("load_collections_async_fallback reason=no_loader")
            self.load_collections()
            self.collections_loaded.emit()
            return
        self.load_collections()

    def import_collections(self) -> None:
        """Run the Import Collection flow (delegated to CollectionImportActions)."""
        self._import_actions.import_collections()

    def _show_import_status(self, message: str) -> None:
        """Show a non-modal preparing cue on the main window status bar if present."""
        window = self._panel.window()
        status_bar = getattr(window, "statusBar", None)
        if callable(status_bar):
            status_bar().showMessage(message)

    def _clear_import_status(self) -> None:
        """Clear the import preparing status message when the cue ends."""
        window = self._panel.window()
        status_bar = getattr(window, "statusBar", None)
        if callable(status_bar):
            status_bar().clearMessage()

    def export_collection(self) -> None:
        """Run the Export Collection flow (delegated to CollectionExportActions)."""
        self._export_actions.export_collection()

    def _export_collection_at_index(self, source_index: QModelIndex) -> None:
        """Export using a clicked tree index (context-menu entry point)."""
        self._export_actions.export_collection(source_index=source_index)

    def restore_tree_state(self) -> None:
        """Re-expands nodes from StateManager state."""
        for collection_id in self._state_manager.get_expanded_collections():
            col_item = self._collection_items_by_id.get(collection_id)
            if col_item is not None:
                self._view.setExpanded(col_item.index(), True)

    def _on_collection_clicked(self, index) -> None:
        item = self._model.itemFromIndex(index)
        data = item.data(Qt.UserRole)
        if isinstance(data, RequestData):
            logger.info(
                "collection_request_opened request_id=%s request_name=%s",
                data.id,
                data.name,
            )
            self.open_request_in_tab.emit(copy_request_for_isolated_tab(data))
        else:
            if self._view.isExpanded(index):
                self._view.collapse(index)
            else:
                self._view.expand(index)

    def remove_item_from_tree(self, item_id: str, item_type: str) -> bool:
        """Removes a collection or request node without rebuilding the full tree model."""
        item = self._find_collection_item(item_id, item_type)
        if item is None:
            return False
        parent = item.parent() or self._model.invisibleRootItem()
        parent.removeRow(item.row())
        if item_type == "collection":
            self._collection_items_by_id.pop(item_id, None)
        logger.info(
            "collection_tree_item_removed item_type=%s item_id=%s",
            item_type,
            item_id,
        )
        return True

    def _find_collection_item(self, item_id: str, item_type: str) -> QStandardItem | None:
        if item_type == "collection":
            return self._collection_items_by_id.get(item_id)
        for row in range(self._model.rowCount()):
            col_item = self._model.item(row)
            for child_row in range(col_item.rowCount()):
                req_item = col_item.child(child_row)
                data = req_item.data(Qt.UserRole)
                if item_type == "request" and isinstance(data, RequestData) and data.id == item_id:
                    return req_item
        return None

    def _is_collection_item(self, index) -> bool:
        """Return True when the tree index refers to a collection (not a request)."""
        item = self._model.itemFromIndex(index)
        if item is None:
            return False
        return isinstance(item.data(Qt.UserRole), str)

    def _on_tree_expanded(self, index) -> None:
        if not self._is_collection_item(index):
            return
        collection_id = self._model.itemFromIndex(index).data(Qt.UserRole)
        current = self._state_manager.get_expanded_collections()
        if collection_id not in current:
            current.append(collection_id)
            self._state_manager.set_expanded_collections(current)

    def _on_tree_collapsed(self, index) -> None:
        if not self._is_collection_item(index):
            return
        collection_id = self._model.itemFromIndex(index).data(Qt.UserRole)
        current = self._state_manager.get_expanded_collections()
        if collection_id in current:
            current.remove(collection_id)
            self._state_manager.set_expanded_collections(current)
