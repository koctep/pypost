"""Shared DisplayRole index lookup for flat and tree views (PYPOST-941/971)."""

from __future__ import annotations

from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt
from PySide6.QtWidgets import QTreeView

__all__ = [
    "display_role_equals",
    "find_child_index_by_display_text",
    "find_tree_index_by_display_text",
]


def display_role_equals(index: QModelIndex, text: str) -> bool:
    """Return True when ``index`` DisplayRole string equals ``text``."""
    return str(index.data(Qt.ItemDataRole.DisplayRole)) == text


def find_child_index_by_display_text(
    model: QAbstractItemModel,
    text: str,
    parent: QModelIndex | None = None,
) -> QModelIndex | None:
    """Return the first column-0 DisplayRole match among direct children."""
    parent_index = QModelIndex() if parent is None else parent
    rows = model.rowCount(parent_index)
    for row in range(rows):
        index = model.index(row, 0, parent_index)
        if not index.isValid():
            continue
        if display_role_equals(index, text):
            return index
    return None


def find_tree_index_by_display_text(tree: QTreeView, text: str) -> QModelIndex | None:
    """Return the first index whose DisplayRole equals ``text``, depth-first."""
    model = tree.model()
    if model is None:
        return None

    def _walk(parent: QModelIndex) -> QModelIndex | None:
        rows = model.rowCount(parent)
        for row in range(rows):
            index = model.index(row, 0, parent)
            if not index.isValid():
                continue
            if display_role_equals(index, text):
                return index
            found = _walk(index)
            if found is not None:
                return found
        return None

    return _walk(QModelIndex())
