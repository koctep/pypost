"""Click helpers for QTreeView rows in agent e2e drive proofs (PYPOST-863)."""

from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QModelIndex, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QTreeView

from pypost.agent.tree_index import find_tree_index_by_display_text

__all__ = [
    "click_tree_row_by_text",
    "find_tree_index_by_text",
]


def find_tree_index_by_text(tree: QTreeView, text: str) -> QModelIndex:
    """Return the first model index whose display text equals ``text``.

    Raises:
        AssertionError: No matching row under the tree model.
    """
    index = find_tree_index_by_display_text(tree, text)
    if index is None or not index.isValid():
        raise AssertionError(f"tree row not found: text={text!r}")
    return index


def click_tree_row_by_text(tree: QTreeView, text: str) -> None:
    """Left-click a tree row by display text via viewport ``visualRect``.

    Tree rows are not widgets, so agent ``ui_click`` cannot target them.
    This helper uses the same ``QTest.mouseClick`` stack as ``ui_actions``.
    """
    index = find_tree_index_by_text(tree, text)
    parent = index.parent()
    if parent.isValid() and not tree.isExpanded(parent):
        tree.expand(parent)
        QCoreApplication.processEvents()
    tree.scrollTo(index)
    QCoreApplication.processEvents()
    rect = tree.visualRect(index)
    assert rect.isValid() and not rect.isEmpty(), f"no visual rect for {text!r}"
    QTest.mouseClick(
        tree.viewport(),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        rect.center(),
    )
    QCoreApplication.processEvents()
