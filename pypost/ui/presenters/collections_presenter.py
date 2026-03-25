import logging

from PySide6.QtWidgets import (
    QTreeView, QMenu, QMessageBox, QAbstractItemDelegate,
)
from PySide6.QtGui import QStandardItemModel, QStandardItem, QIcon
from PySide6.QtCore import QObject, Qt, Signal

from pypost.models.models import RequestData
from pypost.core.request_manager import RequestManager
from pypost.core.state_manager import StateManager
from pypost.core.metrics import MetricsManager

logger = logging.getLogger(__name__)


class CollectionsPresenter(QObject):
    """Owns the collections tree view: loading, rendering, rename, delete, and tab opening."""

    open_request_in_tab = Signal(object)   # payload: RequestData
    open_request_in_isolated_tab = Signal(object)  # payload: RequestData (deep copy)
    collections_changed = Signal()         # after create / delete / rename
    request_renamed = Signal(str, str)     # (request_id, new_name)

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
        self._pending_rename: dict | None = None

        self._model = QStandardItemModel()
        self._view = QTreeView()
        self._view.setHeaderHidden(True)
        self._view.setModel(self._model)
        self._view.clicked.connect(self._on_collection_clicked)
        self._view.setContextMenuPolicy(Qt.CustomContextMenu)
        self._view.customContextMenuRequested.connect(self._show_context_menu)
        self._view.expanded.connect(self._on_tree_expanded)
        self._view.collapsed.connect(self._on_tree_collapsed)
        self._view.itemDelegate().closeEditor.connect(self._on_editor_closed)

    @property
    def widget(self) -> QTreeView:
        return self._view

    def load_collections(self) -> None:
        """(Re)populates tree model from request_manager."""
        self._request_manager.reload_collections()
        self._model.clear()

        collections = self._request_manager.get_collections()
        total_requests = sum(len(col.requests) for col in collections)
        logger.info(
            "load_collections_completed collection_count=%d request_count=%d",
            len(collections), total_requests,
        )

        for col in collections:
            col_item = QStandardItem(col.name)
            col_item.setData(col.id, Qt.UserRole)
            col_item.setEditable(False)
            if 'collection' in self._icons:
                col_item.setIcon(self._icons['collection'])

            for req in col.requests:
                req_item = QStandardItem(f"{req.method} {req.name}")
                req_item.setData(req, Qt.UserRole)
                req_item.setEditable(False)
                if req.method in self._icons:
                    req_item.setIcon(self._icons[req.method])
                col_item.appendRow(req_item)

            self._model.appendRow(col_item)

    def restore_tree_state(self) -> None:
        """Re-expands nodes from StateManager state."""
        root = self._model.invisibleRootItem()
        expanded = self._state_manager.get_expanded_collections()
        for row in range(root.rowCount()):
            item = root.child(row)
            data = item.data(Qt.UserRole)
            if isinstance(data, str) and data in expanded:
                self._view.setExpanded(item.index(), True)

    def _resolve_collection_item_target(self, item: QStandardItem) -> tuple:
        data = item.data(Qt.UserRole)
        if isinstance(data, RequestData):
            return "request", data.id, item.text(), data
        if isinstance(data, str):
            return "collection", data, item.text(), data
        return None, None, item.text(), data

    def _on_collection_clicked(self, index) -> None:
        item = self._model.itemFromIndex(index)
        data = item.data(Qt.UserRole)
        if isinstance(data, RequestData):
            logger.info(
                "collection_request_opened request_id=%s request_name=%s",
                data.id, data.name,
            )
            self.open_request_in_tab.emit(data)
        else:
            if self._view.isExpanded(index):
                self._view.collapse(index)
            else:
                self._view.expand(index)

    def _show_context_menu(self, pos) -> None:
        index = self._view.indexAt(pos)
        if not index.isValid():
            return

        item = self._model.itemFromIndex(index)
        item_type, item_id, item_label, data = self._resolve_collection_item_target(item)
        if not item_type or not item_id:
            return

        menu = QMenu(self._view)

        new_tab_action = None
        if item_type == "request" and isinstance(data, RequestData):
            new_tab_action = menu.addAction("New tab")
            new_tab_action.setToolTip(
                "Open a separate copy of this request; edits in other tabs won't apply here."
            )

        rename_action = menu.addAction("Rename")
        delete_action = menu.addAction("Delete")
        selected_action = menu.exec(self._view.viewport().mapToGlobal(pos))

        if new_tab_action and selected_action == new_tab_action:
            logger.info(
                "collection_request_open_new_tab request_id=%s request_name=%s",
                data.id, data.name,
            )
            self._metrics.track_gui_new_tab_action("collections_context")
            self.open_request_in_isolated_tab.emit(data.model_copy(deep=True))
            return

        if selected_action == rename_action:
            logger.info(
                "collection_item_rename_selected item_type=%s item_id=%s item_label=%s",
                item_type, item_id, item_label,
            )
            self._metrics.track_gui_collection_rename_action(item_type, "selected")
            self._start_rename(index)
            return

        if selected_action != delete_action:
            return

        logger.info(
            "collection_item_delete_selected item_type=%s item_id=%s item_label=%s",
            item_type, item_id, item_label,
        )
        self._metrics.track_gui_collection_delete_action(item_type, "selected")

        reply = QMessageBox.question(
            self._view, "Confirm Delete", f"Delete '{item_label}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            logger.info(
                "collection_item_delete_cancelled item_type=%s item_id=%s",
                item_type, item_id,
            )
            self._metrics.track_gui_collection_delete_action(item_type, "cancelled")
            return

        self._handle_delete(item_id, item_type, item_label)

    def _start_rename(self, index) -> None:
        if self._pending_rename:
            return
        item = self._model.itemFromIndex(index)
        item_type, item_id, _, data = self._resolve_collection_item_target(item)
        if not item_type or not item_id:
            return

        if item_type == "request" and isinstance(data, RequestData):
            item.setText(data.name)

        self._pending_rename = {"item_id": item_id, "item_type": item_type}
        item.setEditable(True)
        self._view.setCurrentIndex(index)
        self._view.edit(index)

    def _on_editor_closed(self, _editor, hint) -> None:
        if not self._pending_rename:
            return

        item_type = self._pending_rename["item_type"]
        item_id = self._pending_rename["item_id"]

        if hint == QAbstractItemDelegate.EndEditHint.RevertModelCache:
            logger.info(
                "collection_item_rename_cancelled item_type=%s item_id=%s",
                item_type, item_id,
            )
            self._metrics.track_gui_collection_rename_action(item_type, "cancelled")
            self._pending_rename = None
            self.load_collections()
            self.restore_tree_state()
            return

        item = self._find_collection_item(item_id, item_type)
        self._pending_rename = None

        if item is None:
            logger.warning(
                "collection_item_rename_not_found_in_model item_type=%s item_id=%s",
                item_type, item_id,
            )
            self._metrics.track_gui_collection_rename_action(item_type, "not_found")
            self.load_collections()
            self.restore_tree_state()
            return

        new_name = item.text().strip()
        if not new_name:
            logger.warning(
                "collection_item_rename_rejected_empty item_type=%s item_id=%s",
                item_type, item_id,
            )
            self._metrics.track_gui_collection_rename_action(item_type, "rejected_empty")
            QMessageBox.warning(self._view, "Rename Error", "Name cannot be empty.")
            self.load_collections()
            self.restore_tree_state()
            return

        try:
            renamed = self._request_manager.rename_collection_item(item_id, item_type, new_name)
        except Exception as exc:
            logger.error(
                "collection_item_rename_failed item_type=%s item_id=%s new_name=%s error=%s",
                item_type, item_id, new_name, exc,
            )
            self._metrics.track_gui_collection_rename_action(item_type, "error")
            QMessageBox.critical(
                self._view, "Rename Error", f"Failed to rename '{item.text()}': {exc}"
            )
            self.load_collections()
            self.restore_tree_state()
            return

        if not renamed:
            logger.warning(
                "collection_item_rename_not_found item_type=%s item_id=%s new_name=%s",
                item_type, item_id, new_name,
            )
            self._metrics.track_gui_collection_rename_action(item_type, "not_found")
            QMessageBox.warning(
                self._view, "Rename Error", f"Could not rename '{item.text()}'."
            )
            self.load_collections()
            self.restore_tree_state()
            return

        logger.info(
            "collection_item_rename_succeeded item_type=%s item_id=%s new_name=%s",
            item_type, item_id, new_name,
        )
        self._metrics.track_gui_collection_rename_action(item_type, "succeeded")

        if item_type == "request":
            self.request_renamed.emit(item_id, new_name)

        self.load_collections()
        self.restore_tree_state()
        self.collections_changed.emit()

    def _find_collection_item(self, item_id: str, item_type: str) -> QStandardItem | None:
        for row in range(self._model.rowCount()):
            col_item = self._model.item(row)
            if item_type == "collection" and col_item.data(Qt.UserRole) == item_id:
                return col_item
            for child_row in range(col_item.rowCount()):
                req_item = col_item.child(child_row)
                data = req_item.data(Qt.UserRole)
                if (
                    item_type == "request"
                    and isinstance(data, RequestData)
                    and data.id == item_id
                ):
                    return req_item
        return None

    def _handle_delete(self, item_id: str, item_type: str, item_label: str) -> None:
        try:
            deleted = self._request_manager.delete_collection_item(item_id, item_type)
        except Exception as exc:
            logger.error(
                "collection_item_delete_failed item_type=%s item_id=%s error=%s",
                item_type, item_id, exc,
            )
            self._metrics.track_gui_collection_delete_action(item_type, "error")
            QMessageBox.critical(
                self._view, "Delete Error", f"Failed to delete '{item_label}': {exc}"
            )
            return

        if not deleted:
            logger.warning(
                "collection_item_delete_not_found item_type=%s item_id=%s",
                item_type, item_id,
            )
            self._metrics.track_gui_collection_delete_action(item_type, "not_found")
            QMessageBox.warning(
                self._view, "Delete Error", f"Could not delete '{item_label}'."
            )
            return

        logger.info(
            "collection_item_delete_succeeded item_type=%s item_id=%s",
            item_type, item_id,
        )
        self._metrics.track_gui_collection_delete_action(item_type, "succeeded")
        self.load_collections()
        self.restore_tree_state()
        self.collections_changed.emit()

    def _on_tree_expanded(self, index) -> None:
        item = self._model.itemFromIndex(index)
        data = item.data(Qt.UserRole)
        if isinstance(data, str):
            current = self._state_manager.get_expanded_collections()
            if data not in current:
                current.append(data)
                self._state_manager.set_expanded_collections(current)

    def _on_tree_collapsed(self, index) -> None:
        item = self._model.itemFromIndex(index)
        data = item.data(Qt.UserRole)
        if isinstance(data, str):
            current = self._state_manager.get_expanded_collections()
            if data in current:
                current.remove(data)
                self._state_manager.set_expanded_collections(current)
