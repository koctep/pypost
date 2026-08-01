"""PYPOST-941: Shared tree DisplayRole walk for ui_select and e2e helper."""

from __future__ import annotations

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QApplication, QTreeView, QWidget

from pypost.agent.tree_index import find_tree_index_by_display_text
from pypost.agent.ui_actions import UiTargetNotInteractableError, ui_select
from tests.helpers.agent_e2e_tree import find_tree_index_by_text

pytestmark = pytest.mark.timeout(30)

_TREE = "fixture_deep_tree"


def _make_three_level_tree(qapp: QApplication) -> tuple[QWidget, QTreeView]:
    root = QWidget()
    tree = QTreeView(root)
    model = QStandardItemModel(tree)
    top = QStandardItem("Top")
    middle = QStandardItem("Middle")
    middle.appendRow(QStandardItem("Grandchild"))
    top.appendRow(middle)
    model.appendRow(top)
    tree.setModel(model)
    tree.setObjectName(_TREE)
    root.show()
    qapp.processEvents()
    return root, tree


def test_e2e_helper_finds_three_level_deep_text(qapp: QApplication) -> None:
    """agent_e2e_tree uses the same recursive DisplayRole walk as ui_select."""
    root, tree = _make_three_level_tree(qapp)
    try:
        index = find_tree_index_by_text(tree, "Grandchild")
        assert index.isValid()
        assert str(index.data(Qt.ItemDataRole.DisplayRole)) == "Grandchild"
    finally:
        root.close()


def test_shared_walk_returns_none_for_missing_text(qapp: QApplication) -> None:
    root, tree = _make_three_level_tree(qapp)
    try:
        assert find_tree_index_by_display_text(tree, "Missing") is None
    finally:
        root.close()


def test_e2e_helper_raises_assertion_not_agent_error(qapp: QApplication) -> None:
    root, tree = _make_three_level_tree(qapp)
    try:
        with pytest.raises(AssertionError, match="tree row not found"):
            find_tree_index_by_text(tree, "Missing")
        with pytest.raises(UiTargetNotInteractableError, match="option not found"):
            ui_select(root, _TREE, "Missing")
    finally:
        root.close()


def test_ui_select_finds_same_deep_index_as_shared_walk(qapp: QApplication) -> None:
    root, tree = _make_three_level_tree(qapp)
    try:
        expected = find_tree_index_by_display_text(tree, "Grandchild")
        assert expected is not None
        ui_select(root, _TREE, "Grandchild")
        assert tree.currentIndex() == expected
    finally:
        root.close()
