"""Shared Qt item-view fixture teardown for model-backed views in tests."""

from __future__ import annotations

from PySide6.QtWidgets import QAbstractItemView, QApplication, QWidget

from pypost.agent.ui_actions import find_widget


def detach_item_view_model(view: QAbstractItemView) -> None:
    """Detach the model before closing to avoid QAbstractItemView destructor noise."""
    if view.model() is not None:
        view.setModel(None)


def close_item_view_fixture(
    root: QWidget,
    qapp: QApplication,
    widget_id: str,
    *,
    view_type: type | tuple[type, ...] = QAbstractItemView,
) -> None:
    """Tear down an isolated model-backed item-view fixture (tree, list view, etc.)."""
    widget = find_widget(root, widget_id)
    if isinstance(widget, view_type):
        detach_item_view_model(widget)
    root.close()
    qapp.processEvents()
