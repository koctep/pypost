"""PYPOST-940: Shared Qt item-view fixture teardown helper."""

from __future__ import annotations

import pytest
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QApplication, QListView, QTreeView

pytestmark = pytest.mark.timeout(30)


def test_detach_item_view_model_clears_model(qapp: QApplication) -> None:
    """Shared helper must detach model before view destruction."""
    from tests.helpers.qt_item_view import detach_item_view_model

    view = QListView()
    model = QStandardItemModel(view)
    model.appendRow(QStandardItem("Row"))
    view.setModel(model)
    assert view.model() is not None

    detach_item_view_model(view)
    assert view.model() is None


def test_close_item_view_fixture_detaches_tree_model(qapp: QApplication) -> None:
    """close_item_view_fixture tears down model-backed tree fixtures safely."""
    from tests.helpers.qt_item_view import close_item_view_fixture

    from PySide6.QtWidgets import QHBoxLayout, QWidget

    from pypost.ui.widget_ids import set_widget_id

    root = QWidget()
    layout = QHBoxLayout(root)
    tree = QTreeView()
    model = QStandardItemModel(tree)
    model.appendRow(QStandardItem("Node"))
    tree.setModel(model)
    set_widget_id(tree, "teardown_tree")
    layout.addWidget(tree)
    root.show()
    qapp.processEvents()

    close_item_view_fixture(root, qapp, "teardown_tree", view_type=QTreeView)
    assert tree.model() is None
