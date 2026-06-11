"""Context-menu actions and rename/delete flows for the collections tree."""

from __future__ import annotations

import logging
from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QAbstractItemDelegate, QMenu, QMessageBox, QTreeView

from pypost.core.metrics import MetricsManager
from pypost.core.request_manager import RequestManager
from pypost.models.models import RequestData

logger = logging.getLogger(__name__)


class CollectionTreeActions:
    """Builds the collections tree context menu and runs rename/delete flows."""

    def __init__(
        self,
        view: QTreeView,
        model: QStandardItemModel,
        request_manager: RequestManager,
        metrics: MetricsManager,
        *,
        find_item: Callable[[str, str], QStandardItem | None],
        remove_item: Callable[[str, str], bool],
        refresh_tree: Callable[[], None],
        restore_tree_state: Callable[[], None],
        emit_collections_changed: Callable[[], None],
        emit_request_renamed: Callable[[str, str], None],
        emit_requests_deleted: Callable[[list], None],
        emit_open_isolated_tab: Callable[[RequestData], None],
    ) -> None:
        self._view = view
        self._model = model
        self._request_manager = request_manager
        self._metrics = metrics
        self._find_item = find_item
        self._remove_item = remove_item
        self._refresh_tree = refresh_tree
        self._restore_tree_state = restore_tree_state
        self._emit_collections_changed = emit_collections_changed
        self._emit_request_renamed = emit_request_renamed
        self._emit_requests_deleted = emit_requests_deleted
        self._emit_open_isolated_tab = emit_open_isolated_tab
        self._pending_rename: dict | None = None

    @property
    def pending_rename(self) -> dict | None:
        return self._pending_rename

    def show_context_menu(self, pos) -> None:
        index = self._view.indexAt(pos)
        if not index.isValid():
            return

        item = self._model.itemFromIndex(index)
        item_type, item_id, item_label, data = self._resolve_item_target(item)
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
                data.id,
                data.name,
            )
            self._metrics.track_gui_new_tab_action("collections_context")
            self._emit_open_isolated_tab(data.model_copy(deep=True))
            return

        if selected_action == rename_action:
            logger.info(
                "collection_item_rename_selected item_type=%s item_id=%s item_label=%s",
                item_type,
                item_id,
                item_label,
            )
            self._metrics.track_gui_collection_rename_action(item_type, "selected")
            self._start_rename(index)
            return

        if selected_action != delete_action:
            return

        logger.info(
            "collection_item_delete_selected item_type=%s item_id=%s item_label=%s",
            item_type,
            item_id,
            item_label,
        )
        self._metrics.track_gui_collection_delete_action(item_type, "selected")

        reply = QMessageBox.question(
            self._view,
            "Confirm Delete",
            f"Delete '{item_label}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            logger.info(
                "collection_item_delete_cancelled item_type=%s item_id=%s",
                item_type,
                item_id,
            )
            self._metrics.track_gui_collection_delete_action(item_type, "cancelled")
            return

        self.handle_delete(item_id, item_type, item_label)

    def _start_rename(self, index) -> None:
        if self._pending_rename:
            return
        item = self._model.itemFromIndex(index)
        item_type, item_id, _, data = self._resolve_item_target(item)
        if not item_type or not item_id:
            return

        if item_type == "request" and isinstance(data, RequestData):
            item.setText(data.name)

        self._pending_rename = {"item_id": item_id, "item_type": item_type}
        item.setEditable(True)
        self._view.setCurrentIndex(index)
        self._view.edit(index)

    def on_editor_closed(self, _editor, hint) -> None:
        if not self._pending_rename:
            return

        item_type = self._pending_rename["item_type"]
        item_id = self._pending_rename["item_id"]

        if hint == QAbstractItemDelegate.EndEditHint.RevertModelCache:
            logger.info(
                "collection_item_rename_cancelled item_type=%s item_id=%s",
                item_type,
                item_id,
            )
            self._metrics.track_gui_collection_rename_action(item_type, "cancelled")
            self._pending_rename = None
            self._finish_rename_tree_update(item_id, item_type)
            return

        item = self._find_item(item_id, item_type)
        self._pending_rename = None

        if item is None:
            logger.warning(
                "collection_item_rename_not_found_in_model item_type=%s item_id=%s",
                item_type,
                item_id,
            )
            self._metrics.track_gui_collection_rename_action(item_type, "not_found")
            self._finish_rename_tree_update(item_id, item_type)
            return

        new_name = item.text().strip()
        if not new_name:
            logger.warning(
                "collection_item_rename_rejected_empty item_type=%s item_id=%s",
                item_type,
                item_id,
            )
            self._metrics.track_gui_collection_rename_action(item_type, "rejected_empty")
            QMessageBox.warning(self._view, "Rename Error", "Name cannot be empty.")
            self._finish_rename_tree_update(item_id, item_type, item)
            return

        try:
            renamed = self._request_manager.rename_collection_item(item_id, item_type, new_name)
        except Exception as exc:
            logger.error(
                "collection_item_rename_failed item_type=%s item_id=%s new_name=%s error=%s",
                item_type,
                item_id,
                new_name,
                exc,
            )
            self._metrics.track_gui_collection_rename_action(item_type, "error")
            QMessageBox.critical(
                self._view, "Rename Error", f"Failed to rename '{item.text()}': {exc}"
            )
            self._finish_rename_tree_update(item_id, item_type, item)
            return

        if not renamed:
            logger.warning(
                "collection_item_rename_not_found item_type=%s item_id=%s new_name=%s",
                item_type,
                item_id,
                new_name,
            )
            self._metrics.track_gui_collection_rename_action(item_type, "not_found")
            QMessageBox.warning(self._view, "Rename Error", f"Could not rename '{item.text()}'.")
            self._finish_rename_tree_update(item_id, item_type, item)
            return

        logger.info(
            "collection_item_rename_succeeded item_type=%s item_id=%s new_name=%s",
            item_type,
            item_id,
            new_name,
        )
        self._metrics.track_gui_collection_rename_action(item_type, "succeeded")

        if item_type == "request":
            self._emit_request_renamed(item_id, new_name)

        self._finish_rename_tree_update(item_id, item_type, item, new_name=new_name)
        self._emit_collections_changed()

    def handle_delete(self, item_id: str, item_type: str, item_label: str) -> None:
        affected_request_ids = self._affected_request_ids(item_id, item_type)
        try:
            deleted = self._request_manager.delete_collection_item(item_id, item_type)
        except Exception as exc:
            logger.error(
                "collection_item_delete_failed item_type=%s item_id=%s error=%s",
                item_type,
                item_id,
                exc,
            )
            self._metrics.track_gui_collection_delete_action(item_type, "error")
            QMessageBox.critical(
                self._view, "Delete Error", f"Failed to delete '{item_label}': {exc}"
            )
            return

        if not deleted:
            logger.warning(
                "collection_item_delete_not_found item_type=%s item_id=%s",
                item_type,
                item_id,
            )
            self._metrics.track_gui_collection_delete_action(item_type, "not_found")
            QMessageBox.warning(self._view, "Delete Error", f"Could not delete '{item_label}'.")
            return

        logger.info(
            "collection_item_delete_succeeded item_type=%s item_id=%s",
            item_type,
            item_id,
        )
        self._metrics.track_gui_collection_delete_action(item_type, "succeeded")
        if affected_request_ids:
            self._emit_requests_deleted(affected_request_ids)
        if not self._remove_item(item_id, item_type):
            self._refresh_tree()
            self._restore_tree_state()
        self._emit_collections_changed()

    def _resolve_item_target(self, item: QStandardItem) -> tuple:
        data = item.data(Qt.UserRole)
        if isinstance(data, RequestData):
            return "request", data.id, item.text(), data
        if isinstance(data, str):
            return "collection", data, item.text(), data
        return None, None, item.text(), data

    def _canonical_item_label(self, item_id: str, item_type: str) -> str | None:
        for col in self._request_manager.get_collections():
            if item_type == "collection" and col.id == item_id:
                return col.name
            if item_type == "request":
                for req in col.requests:
                    if req.id == item_id:
                        return f"{req.method} {req.name}"
        return None

    def _sync_rename_tree_item(
        self,
        item: QStandardItem,
        item_id: str,
        item_type: str,
        *,
        new_name: str | None = None,
    ) -> None:
        item.setEditable(False)
        if new_name is not None:
            if item_type == "request":
                for col in self._request_manager.get_collections():
                    for req in col.requests:
                        if req.id == item_id:
                            item.setData(req, Qt.UserRole)
                            item.setText(f"{req.method} {req.name}")
                            return
            else:
                item.setText(new_name)
            return

        label = self._canonical_item_label(item_id, item_type)
        if label is not None:
            item.setText(label)

    def _finish_rename_tree_update(
        self,
        item_id: str,
        item_type: str,
        item: QStandardItem | None = None,
        *,
        new_name: str | None = None,
    ) -> None:
        if item is None:
            item = self._find_item(item_id, item_type)
        if item is None:
            logger.warning(
                "collection_item_rename_tree_sync_fallback item_type=%s item_id=%s",
                item_type,
                item_id,
            )
            self._refresh_tree()
            self._restore_tree_state()
            return
        self._sync_rename_tree_item(item, item_id, item_type, new_name=new_name)

    def _affected_request_ids(self, item_id: str, item_type: str) -> list[str]:
        if item_type == "request":
            return [item_id]
        if item_type == "collection":
            for col in self._request_manager.get_collections():
                if col.id == item_id:
                    return [req.id for req in col.requests]
        return []
