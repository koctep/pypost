"""Export Collection orchestration for the collections sidebar (PYPOST-989).

Split out of ``CollectionsPresenter`` the same way ``CollectionImportActions`` is:
the presenter owns the tree and the panel, this owns the selection → save dialog
→ write → result flow. Payload shaping lives in the Qt-free
``pypost.core.collection_export`` module.
"""
from __future__ import annotations

import logging
from collections.abc import Callable

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import QTreeView, QWidget

from pypost.core.collection_export import (
    CollectionExportError,
    CollectionExportResult,
    build_export_payload,
    collection_for_export,
    format_export_result,
    suggested_export_filename,
    write_export_file,
)
from pypost.core.request_manager import RequestManager
from pypost.models.models import Collection, RequestData
from pypost.ui.collection_item_dialogs import (
    prompt_export_collection_file,
    show_collection_export_error,
    show_collection_export_no_selection_error,
    show_collection_export_result,
)

logger = logging.getLogger(__name__)

SerializeCollection = Callable[[Collection], dict]


class CollectionExportActions:
    """Runs one Export Collection interaction end to end."""

    def __init__(
        self,
        parent: QWidget,
        tree_view: QTreeView,
        model: QStandardItemModel,
        request_manager: RequestManager,
        *,
        serialize_collection: SerializeCollection | None = build_export_payload,
    ) -> None:
        self._parent = parent
        self._tree = tree_view
        self._model = model
        self._request_manager = request_manager
        self._serialize_collection = serialize_collection

    def export_collection(self, source_index: QModelIndex | None = None) -> None:
        """Write a collection (with requests) to a user-chosen file.

        When ``source_index`` is omitted, uses the tree's ``currentIndex()``
        (below-tree button). Context-menu callers pass the clicked index.
        """
        if self._serialize_collection is None:
            return

        index = self._tree.currentIndex() if source_index is None else source_index
        collection_id = _selected_collection_id(self._model, index)
        target = collection_for_export(
            self._request_manager.get_collections(),
            selected_collection_id=collection_id,
        )
        if target is None:
            logger.warning("collection_export_no_selection")
            show_collection_export_no_selection_error(self._parent)
            return

        suggested_name = suggested_export_filename(target)
        path = prompt_export_collection_file(self._parent, suggested_name=suggested_name)
        if path is None:
            return

        try:
            payload = self._serialize_collection(target)
            write_export_file(path, payload)
        except CollectionExportError as exc:
            logger.warning("collection_export_failed reason=%s", exc)
            show_collection_export_error(self._parent, str(exc))
            return

        result = CollectionExportResult(
            collection_name=target.name,
            request_count=len(target.requests),
            path=path,
        )
        logger.info(
            "collection_export_completed collection_name=%s request_count=%d path=%s",
            result.collection_name,
            result.request_count,
            result.path,
        )
        show_collection_export_result(
            self._parent,
            format_export_result(result),
            success=True,
        )


def _selected_collection_id(
    model: QStandardItemModel, index: QModelIndex
) -> str | None:
    """Resolve the tree's current index to a collection id, if any."""
    if not index.isValid():
        return None
    item = model.itemFromIndex(index)
    if item is None:
        return None
    data = item.data(Qt.ItemDataRole.UserRole)
    if isinstance(data, str):
        return data
    if isinstance(data, RequestData):
        parent = item.parent()
        if parent is not None:
            parent_data = parent.data(Qt.ItemDataRole.UserRole)
            if isinstance(parent_data, str):
                return parent_data
    return None
