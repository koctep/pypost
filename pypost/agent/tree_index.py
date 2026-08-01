"""Shared QTreeView DisplayRole index lookup (PYPOST-941)."""

from __future__ import annotations

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtWidgets import QTreeView

__all__ = ["find_tree_index_by_display_text"]


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
            if str(index.data(Qt.ItemDataRole.DisplayRole)) == text:
                return index
            found = _walk(index)
            if found is not None:
                return found
        return None

    return _walk(QModelIndex())
