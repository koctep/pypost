"""Shared Qt window activation and key simulation test helper."""

from __future__ import annotations

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLineEdit, QVBoxLayout, QWidget

ACTIVATION_SKIP: str = "window activation unavailable on this QPA platform"


def activate_window(
    window: QWidget,
    focus_target: QWidget | None = None,
    *,
    timeout_ms: int = 2000,
) -> None:
    """Show and activate window, skipping if QPA platform cannot activate it."""
    window.show()
    window.activateWindow()
    if not QTest.qWaitForWindowActive(window, timeout_ms):
        pytest.skip(ACTIVATION_SKIP)
    if focus_target is not None:
        focus_target.setFocus()
    QApplication.processEvents()


def click_key(
    target: QWidget,
    key: Qt.Key,
    modifier: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
) -> None:
    """Simulate key click on target widget and process pending Qt events."""
    QTest.keyClick(target, key, modifier)
    QApplication.processEvents()


class ActivatedWindow:
    """Context manager setting up a bare window with focused QLineEdit for key tests."""

    def __init__(self, *, timeout_ms: int = 2000) -> None:
        self.timeout_ms = timeout_ms
        self.window = QWidget()
        self.line_edit = QLineEdit(self.window)
        QVBoxLayout(self.window).addWidget(self.line_edit)

    def __enter__(self) -> ActivatedWindow:
        return self

    def activate(self) -> None:
        activate_window(self.window, self.line_edit, timeout_ms=self.timeout_ms)

    def click(
        self,
        key: Qt.Key,
        modifier: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
    ) -> None:
        click_key(self.line_edit, key, modifier)

    def __exit__(self, *_exc: object) -> None:
        self.window.close()
        QApplication.processEvents()
        self.window.deleteLater()
        QApplication.processEvents()
