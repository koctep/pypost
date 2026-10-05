import pytest
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QWidget

from pypost.ui.hotkeys import (
    collect_hotkey_rows,
    format_shortcut_display,
    register_hotkey,
    register_hotkey_group,
    tag_action,
)
from tests.helpers.qt_activation import ActivatedWindow as _ActivatedWindow

pytestmark = pytest.mark.timeout(30)

def test_format_shortcut_display_joins_alternatives():
    assert format_shortcut_display(["F5", "Ctrl+Return"]) == "F5 / Ctrl+Return"

def test_format_shortcut_display_collapses_range():
    keys = [f"Alt+{index}" for index in range(1, 10)]
    assert format_shortcut_display(keys, collapse=True) == "Alt+1 ... Alt+9"

def test_collect_hotkey_rows_from_registered_actions(qapp):
    root = QWidget()
    register_hotkey(
        root,
        section="General",
        label="Settings",
        keys=("Ctrl+,", "F12"),
        slot=lambda: None,
        order=2,
    )
    quit_action = QAction("Quit", root)
    root.addAction(quit_action)
    tag_action(
        quit_action,
        section="General",
        order=1,
        keys=("Ctrl+Q",),
        label="Quit Application",
    )

    rows = collect_hotkey_rows(root)
    assert rows[0] == ("General", "")
    labels = [label for label, _ in rows if _]
    assert labels == ["Quit Application", "Settings"]
    settings_row = next(value for label, value in rows if label == "Settings")
    assert "Ctrl+," in settings_row
    assert "F12" in settings_row

def test_register_hotkey_group_collapsed_display(qapp):
    root = QWidget()
    register_hotkey_group(
        root,
        section="Tabs",
        label="Switch to Tab 1-9",
        bindings=tuple((f"Alt+{index}", lambda: None) for index in range(1, 10)),
        order=1,
    )

    rows = collect_hotkey_rows(root)
    shortcut = next(value for label, value in rows if label == "Switch to Tab 1-9")
    assert shortcut == "Alt+1 ... Alt+9"

def test_hotkeys_dialog_uses_parent_actions(qapp):
    from pypost.ui.dialogs.hotkeys_dialog import HotkeysDialog

    root = QWidget()
    register_hotkey(
        root,
        section="Tabs",
        label="New Tab",
        keys=("Ctrl+N",),
        slot=lambda: None,
        order=1,
    )

    dialog = HotkeysDialog(root)
    table_labels = [
        dialog.table.item(row, 0).text()
        for row in range(dialog.table.rowCount())
        if dialog.table.item(row, 1).text()
    ]
    assert "New Tab" in table_labels


# ---------------------------------------------------------------------------
# PYPOST-1285: documentation rows must not make real shortcuts ambiguous
# ---------------------------------------------------------------------------

def test_documentation_row_does_not_make_bound_shortcut_ambiguous(qapp):
    """E1: F5 / Ctrl+Return doc rows leave the real binding unambiguous."""
    from unittest.mock import MagicMock

    from PySide6.QtCore import Qt

    from pypost.ui.hotkeys import register_hotkey_documentation

    spy = MagicMock()
    with _ActivatedWindow() as ctx:
        register_hotkey(
            ctx.window,
            section="Request Editor",
            label="Send Request",
            keys=("F5", "Ctrl+Return"),
            slot=spy,
            order=1,
        )
        register_hotkey_documentation(
            ctx.window, section="WebSocket Session", label="Connect / Disconnect",
            keys=("F5",), order=1,
        )
        register_hotkey_documentation(
            ctx.window, section="WebSocket Session", label="Send Message",
            keys=("Ctrl+Return",), order=2,
        )
        ctx.activate()
        ctx.click(Qt.Key.Key_F5)
        assert spy.call_count == 1, "F5 did not reach the bound slot (ambiguous)"
        ctx.click(Qt.Key.Key_Return, Qt.KeyboardModifier.ControlModifier)
        assert spy.call_count == 2, "Ctrl+Return did not reach the bound slot (ambiguous)"


def test_documentation_row_displays_native_text(qapp):
    """E2: a doc row shows the native Ctrl+Return text."""
    from PySide6.QtGui import QKeySequence

    from pypost.ui.hotkeys import register_hotkey_documentation

    root = QWidget()
    register_hotkey_documentation(
        root, section="WebSocket Session", label="Send Message",
        keys=("Ctrl+Return",), order=1,
    )
    rows = collect_hotkey_rows(root)
    native = QKeySequence("Ctrl+Return").toString(QKeySequence.SequenceFormat.NativeText)
    assert ("Send Message", native) in rows


def test_focus_url_ctrl_l_not_ambiguous_with_protocol_doc_rows(qapp):
    """E3: Ctrl+L and Alt+D reach Focus URL Bar despite protocol doc rows."""
    from unittest.mock import MagicMock

    from PySide6.QtCore import Qt

    from pypost.ui.main_window_protocol_hotkeys import register_protocol_session_hotkeys

    spy = MagicMock()
    with _ActivatedWindow() as ctx:
        register_hotkey(
            ctx.window,
            section="Request Editor",
            label="Focus URL Bar",
            keys=("Ctrl+L", "Alt+D"),
            slot=spy,
            order=4,
        )
        register_protocol_session_hotkeys(ctx.window, MagicMock())
        ctx.activate()
        ctx.click(Qt.Key.Key_D, Qt.KeyboardModifier.AltModifier)
        assert spy.call_count == 1, "Alt+D guard regressed"
        ctx.click(Qt.Key.Key_L, Qt.KeyboardModifier.ControlModifier)
        assert spy.call_count == 2, "Ctrl+L did not reach the bound slot (ambiguous)"
