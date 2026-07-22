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
