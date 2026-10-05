"""Tests for shared Qt window activation and key simulation helper (PYPOST-1292)."""

from __future__ import annotations

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLineEdit, QWidget

from tests.helpers.qt_activation import (
    ACTIVATION_SKIP,
    ActivatedWindow,
    activate_window,
    click_key,
)

pytestmark = pytest.mark.timeout(30)


def test_activation_skip_constant_is_non_empty_string() -> None:
    """ACTIVATION_SKIP must match standard skip message."""
    assert isinstance(ACTIVATION_SKIP, str)
    assert ACTIVATION_SKIP == "window activation unavailable on this QPA platform"


def test_activate_window_and_click_key(qapp: QApplication) -> None:
    """activate_window and click_key operate on arbitrary QWidget and focus child."""
    window = QWidget()
    line_edit = QLineEdit(window)
    try:
        activate_window(window, focus_target=line_edit, timeout_ms=2000)
        assert line_edit.hasFocus()

        click_key(line_edit, Qt.Key.Key_A)
        assert line_edit.text() == "a"
    finally:
        window.close()
        qapp.processEvents()
        window.deleteLater()
        qapp.processEvents()


def test_activated_window_context_manager(qapp: QApplication) -> None:
    """ActivatedWindow context manager sets up a focused QLineEdit and simulates keys."""
    with ActivatedWindow(timeout_ms=2000) as harness:
        harness.activate()
        assert harness.line_edit.hasFocus()

        harness.click(Qt.Key.Key_B)
        assert harness.line_edit.text() == "b"
