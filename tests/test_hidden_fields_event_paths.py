"""Keyboard and context-menu interaction coverage for PYPOST-1531."""

from collections.abc import Iterator
from typing import Any

import pytest
from PySide6.QtCore import QCoreApplication, QItemSelectionModel, QPoint, Qt
from PySide6.QtGui import QAction, QContextMenuEvent
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QLineEdit, QMenu

from pypost.ui.widgets.hidden_fields_table import HiddenFieldsTable

pytestmark = pytest.mark.timeout(30)

_SELECT_ROWS = (
    QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows
)


@pytest.fixture
def table(qapp: Any) -> Iterator[HiddenFieldsTable]:
    widget = HiddenFieldsTable()
    widget.set_data(["password", "user.token", "secret"])
    widget.show()
    try:
        yield widget
    finally:
        widget.close()
        widget.deleteLater()


def _select_rows(table: HiddenFieldsTable, rows: list[int]) -> None:
    selection = table.selectionModel()
    assert selection is not None
    selection.clearSelection()
    model = table.model()
    assert model is not None
    for row in rows:
        selection.select(model.index(row, 0), _SELECT_ROWS)


def _assert_rows(table: HiddenFieldsTable, selectors: list[str]) -> None:
    assert table.get_data() == selectors
    assert table.rowCount() == len(selectors) + 1
    trailing = table.item(len(selectors), 0)
    assert trailing is not None
    assert trailing.text() == ""


def _dispatch_menu(
    table: HiddenFieldsTable, monkeypatch: pytest.MonkeyPatch, choice: str | None,
    *, removal_enabled: bool,
) -> None:
    opened: list[bool] = []
    original_init = QMenu.__init__

    def init_with_chooser(menu: QMenu, *args: Any, **kwargs: Any) -> None:
        original_init(menu, *args, **kwargs)

        def exec_choice(
            _position: QPoint, _at: QAction | None = None,
        ) -> QAction | None:
            opened.append(True)
            actions = {action.text(): action for action in menu.actions()}
            assert list(actions) == ["Add Selector", "Remove Selected"]
            assert actions["Add Selector"].isEnabled()
            assert actions["Remove Selected"].isEnabled() is removal_enabled
            if choice is None:
                return None
            return actions[choice]

        # Shiboken resolves QMenu.exec on the instance, so a class patch never
        # reaches the handler and the real modal loop would block the test.
        menu.exec = exec_choice

    monkeypatch.setattr(QMenu, "__init__", init_with_chooser)
    position = QPoint(5, 5)
    event = QContextMenuEvent(
        QContextMenuEvent.Reason.Mouse, position, table.viewport().mapToGlobal(position),
    )
    QCoreApplication.sendEvent(table.viewport(), event)
    assert opened == [True]


@pytest.mark.parametrize("key", [Qt.Key.Key_Delete, Qt.Key.Key_Backspace])
def test_keyboard_removes_selected_rows(table: HiddenFieldsTable, key: Qt.Key) -> None:
    _select_rows(table, [0, 2])
    data_changed = QSignalSpy(table.data_changed)
    changed = QSignalSpy(table.changed)

    QTest.keyClick(table, key)

    _assert_rows(table, ["user.token"])
    assert data_changed.count() == 1
    assert changed.count() == 1


@pytest.mark.parametrize("key", [Qt.Key.Key_Delete, Qt.Key.Key_Backspace])
def test_keyboard_keeps_trailing_row(table: HiddenFieldsTable, key: Qt.Key) -> None:
    _select_rows(table, [3])
    changed = QSignalSpy(table.changed)

    QTest.keyClick(table, key)

    _assert_rows(table, ["password", "user.token", "secret"])
    assert changed.count() == 0


@pytest.mark.parametrize("key", [Qt.Key.Key_Delete, Qt.Key.Key_Backspace])
def test_keyboard_does_not_remove_row_during_editing(
    table: HiddenFieldsTable, key: Qt.Key,
) -> None:
    model = table.model()
    assert model is not None
    table.setCurrentIndex(model.index(0, 0))
    table.edit(table.currentIndex())
    assert table.state() == HiddenFieldsTable.State.EditingState
    editor = table.findChild(QLineEdit)
    assert editor is not None

    QTest.keyClick(table, key)

    _assert_rows(table, ["password", "user.token", "secret"])
    QTest.keyClick(editor, Qt.Key.Key_Escape)


def test_context_menu_removes_selected_rows(
    table: HiddenFieldsTable, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _select_rows(table, [0, 2])
    data_changed = QSignalSpy(table.data_changed)
    changed = QSignalSpy(table.changed)

    _dispatch_menu(table, monkeypatch, "Remove Selected", removal_enabled=True)

    _assert_rows(table, ["user.token"])
    assert data_changed.count() == 1
    assert changed.count() == 1


@pytest.mark.parametrize("selected", [False, True])
def test_context_menu_cancellation_preserves_rows(
    table: HiddenFieldsTable, monkeypatch: pytest.MonkeyPatch, selected: bool,
) -> None:
    _select_rows(table, [0] if selected else [])
    changed = QSignalSpy(table.changed)

    _dispatch_menu(table, monkeypatch, None, removal_enabled=selected)

    _assert_rows(table, ["password", "user.token", "secret"])
    assert changed.count() == 0


def test_context_menu_add_edits_and_commits_trailing_row(
    table: HiddenFieldsTable, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _select_rows(table, [])
    _dispatch_menu(table, monkeypatch, "Add Selector", removal_enabled=False)
    assert table.currentIndex().row() == 3
    assert table.state() == HiddenFieldsTable.State.EditingState
    editor = table.findChild(QLineEdit)
    assert editor is not None

    QTest.keyClicks(editor, "session.token")
    assert editor.text() == "session.token"
    QTest.keyClick(editor, Qt.Key.Key_Return)
    # Commit and closeEditor are queued so the editor is not destroyed mid-event.
    QCoreApplication.processEvents()

    _assert_rows(table, ["password", "user.token", "secret", "session.token"])
