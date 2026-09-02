"""PYPOST-1246: headless focus, IME, and window-deactivation coverage."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QInputMethodEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLineEdit, QVBoxLayout, QWidget

from pypost.ui.widgets.variable_autocomplete_line_edit import (
    VariableAutocompleteLineEdit,
)

pytestmark = pytest.mark.timeout(60)


def _shown_editor_window(qapp: QApplication) -> tuple[QWidget, VariableAutocompleteLineEdit,
                                                        QLineEdit]:
    """Create a visible offscreen window with an editor and focus target."""
    window = QWidget()
    layout = QVBoxLayout(window)
    editor = VariableAutocompleteLineEdit(["API_KEY", "PUBLIC_HOST"])
    focus_target = QLineEdit()
    layout.addWidget(editor)
    layout.addWidget(focus_target)
    window.resize(360, 120)
    window.show()
    assert QTest.qWaitForWindowExposed(window)
    qapp.processEvents()
    return window, editor, focus_target


def _open_popup(qapp: QApplication, editor: VariableAutocompleteLineEdit) -> None:
    """Open the editor popup through the normal text-triggered completion path."""
    # A tooltip window does not steal activation on the offscreen Qt platform. The
    # production popup remains a Qt.Popup; this keeps the fixture focused on events.
    editor._popup.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
    editor.setFocus()
    editor.setText("{{ API")
    editor.setCursorPosition(len(editor.text()))
    editor.trigger_autocomplete()
    assert editor.is_popup_visible()
    assert editor.current_candidates() == ["API_KEY"]


@pytest.mark.usefixtures("qapp")
def test_popup_dismisses_after_rapid_focus_shifts(qapp: QApplication) -> None:
    """Rapid editor-to-peer focus changes do not leave a stale popup visible."""
    window, editor, focus_target = _shown_editor_window(qapp)
    try:
        _open_popup(qapp, editor)
        for _ in range(3):
            focus_target.setFocus(Qt.FocusReason.OtherFocusReason)
            qapp.processEvents()
            assert not editor.is_popup_visible()
            editor.setFocus(Qt.FocusReason.OtherFocusReason)
            qapp.processEvents()
            _open_popup(qapp, editor)
    finally:
        window.close()


@pytest.mark.usefixtures("qapp")
def test_ime_composition_is_safe_while_popup_is_open(qapp: QApplication) -> None:
    """IME preedit input is handled without corrupting completion or crashing Qt."""
    window, editor, focus_target = _shown_editor_window(qapp)
    try:
        _open_popup(qapp, editor)
        composition = QInputMethodEvent("候補", [])
        QApplication.sendEvent(editor, composition)
        qapp.processEvents()
        assert composition.isAccepted()
        assert editor.text() == "{{ API"

        focus_target.setFocus(Qt.FocusReason.OtherFocusReason)
        qapp.processEvents()
        assert not editor.is_popup_visible()
    finally:
        window.close()


@pytest.mark.usefixtures("qapp")
def test_window_deactivation_preserves_popup_state_without_crashing(qapp: QApplication) -> None:
    """Window deactivation while completing does not corrupt the popup state."""
    window, editor, _focus_target = _shown_editor_window(qapp)
    try:
        _open_popup(qapp, editor)
        QApplication.sendEvent(window, QEvent(QEvent.Type.WindowDeactivate))
        QApplication.sendEvent(editor._popup, QEvent(QEvent.Type.WindowDeactivate))
        qapp.processEvents()
        assert editor.is_popup_visible()
        assert editor.current_candidates() == ["API_KEY"]
        editor.dismiss_popup()
        assert not editor.is_popup_visible()
    finally:
        window.close()
