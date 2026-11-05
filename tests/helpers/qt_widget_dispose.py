"""Shared Qt top-level widget dispose for GUI test fixtures.

Used by environment export (PYPOST-1315), collection export (PYPOST-1357),
and environment list/import (PYPOST-1358) suites that create unparented
Qt roots and must drain DeferredDelete while ``qapp`` is still alive.
"""

from __future__ import annotations

from typing import Any

import shiboken6
from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QAbstractItemView, QApplication, QWidget


def dispose_qt_root(widget: QWidget | None, qapp: QApplication) -> None:
    """Destroy a top-level Qt root while ``qapp`` is alive.

    Sequence: close → ``processEvents`` → ``deleteLater`` → drain
    ``QEvent.Type.DeferredDelete`` via ``sendPostedEvents`` → ``processEvents``.

    ``processEvents`` alone does not process DeferredDelete for roots such as
    ``EnvironmentListWidget``; ``sendPostedEvents`` is required for
    ``shiboken6.isValid`` to become False before process exit.
    Idempotent if the C++ object is already gone.
    """
    if widget is None or not shiboken6.isValid(widget):
        return
    widget.close()
    qapp.processEvents()
    if not shiboken6.isValid(widget):
        return
    widget.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qapp.processEvents()


def dispose_collections_export_fixture(presenter: Any, qapp: QApplication) -> None:
    """Fence collections presenter lifecycle and dispose the export UI panel root."""
    teardown = getattr(presenter, "teardown", None)
    if callable(teardown):
        teardown(timeout_ms=50)
    tree = getattr(presenter, "widget", None)
    if isinstance(tree, QAbstractItemView) and shiboken6.isValid(tree):
        if tree.model() is not None:
            tree.setModel(None)
    panel = getattr(presenter, "panel", None)
    dispose_qt_root(panel if isinstance(panel, QWidget) else None, qapp)
