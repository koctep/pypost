import logging

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QTreeView

from pypost.core.metrics import MetricsManager
from pypost.core.request_sync import copy_request_for_isolated_tab
from pypost.core.request_manager import RequestManager
from pypost.core.state_manager import StateManager
from pypost.models.models import RequestData
from pypost.ui.delegates import CollectionItemRenameDelegate
from pypost.ui.presenters.collection_tree_actions import CollectionTreeActions

logger = logging.getLogger(__name__)


class CollectionsPresenter(QObject):
    """Owns the collections tree view: loading, rendering, rename, delete, and tab opening."""

    open_request_in_tab = Signal(object)  # payload: RequestData (deep copy for new tab)
    open_request_in_isolated_tab = Signal(object)  # payload: RequestData (deep copy)
    collections_changed = Signal()  # after create / delete / rename
    request_renamed = Signal(str, str)  # (request_id, new_name)
    requests_deleted = Signal(list)  # request IDs whose tabs should close

    def __init__(
        self,
        request_manager: RequestManager,
        state_manager: StateManager,
        metrics: MetricsManager,
        icons: dict,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._request_manager = request_manager
        self._state_manager = state_manager
        self._metrics = metrics
        self._icons = icons

        self._model = QStandardItemModel()
        self._view = QTreeView()
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

    @property
    def widget(self) -> QTreeView:
        return self._view

    @property
    def _pending_rename(self) -> dict | None:
        return self._tree_actions.pending_rename

    @_pending_rename.setter
    def _pending_rename(self, value: dict | None) -> None:
        self._tree_actions._pending_rename = value

    def refresh_tree(self) -> None:
        """Rebuilds tree model from RequestManager in-memory collections."""
        self._model.clear()

        collections = self._request_manager.get_collections()
        total_requests = sum(len(col.requests) for col in collections)
        logger.info(
            "refresh_tree_completed collection_count=%d request_count=%d",
            len(collections),
            total_requests,
        )

        for col in collections:
            col_item = QStandardItem(col.name)
            col_item.setData(col.id, Qt.UserRole)
            col_item.setEditable(False)
            if "collection" in self._icons:
                col_item.setIcon(self._icons["collection"])

            for req in col.requests:
                req_item = QStandardItem(f"{req.method} {req.name}")
                req_item.setData(req, Qt.UserRole)
                req_item.setEditable(False)
                if req.method in self._icons:
                    req_item.setIcon(self._icons[req.method])
                col_item.appendRow(req_item)

            self._model.appendRow(col_item)

    def load_collections(self) -> None:
        """Reloads collections from storage and rebuilds the tree model."""
        self._request_manager.reload_collections()
        self.refresh_tree()

    def restore_tree_state(self) -> None:
        """Re-expands nodes from StateManager state."""
        root = self._model.invisibleRootItem()
        expanded = self._state_manager.get_expanded_collections()
        for row in range(root.rowCount()):
            item = root.child(row)
            if self._is_collection_item(item.index()) and item.data(Qt.UserRole) in expanded:
                self._view.setExpanded(item.index(), True)

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
        logger.info(
            "collection_tree_item_removed item_type=%s item_id=%s",
            item_type,
            item_id,
        )
        return True

    def _find_collection_item(self, item_id: str, item_type: str) -> QStandardItem | None:
        for row in range(self._model.rowCount()):
            col_item = self._model.item(row)
            if item_type == "collection" and col_item.data(Qt.UserRole) == item_id:
                return col_item
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
