"""PYPOST-836: Agent UI action primitives — fixture + main-window subset."""

from __future__ import annotations

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QListView,
    QListWidget,
    QPushButton,
    QTreeView,
    QWidget,
)

from pypost.agent.lifecycle import AgentAppSession
from pypost.agent.ui_actions import (
    UiTargetNotFoundError,
    UiTargetNotInteractableError,
    find_widget,
    ui_click,
    ui_fill,
    ui_select,
    ui_send_key,
)
from pypost.ui.widget_ids import METHOD_COMBO, URL_INPUT, set_widget_id
from tests.helpers.qt_item_view import close_item_view_fixture

pytestmark = [
    pytest.mark.timeout(60),
    pytest.mark.agent_e2e,
]

_BTN = "fixture_click_btn"
_INPUT = "fixture_line_edit"
_COMBO = "fixture_combo"
_LIST = "fixture_list"
_LIST_VIEW = "fixture_list_view"
_TREE = "fixture_tree"
_DISABLED = "fixture_disabled_btn"


def _make_fixture(qapp: QApplication) -> tuple[QWidget, list[int]]:
    root = QWidget()
    layout = QHBoxLayout(root)
    clicks: list[int] = [0]

    btn = QPushButton("Go")

    def _on_click() -> None:
        clicks[0] += 1

    btn.clicked.connect(_on_click)
    set_widget_id(btn, _BTN)
    layout.addWidget(btn)

    line = QLineEdit()
    set_widget_id(line, _INPUT)
    layout.addWidget(line)

    combo = QComboBox()
    combo.addItems(["GET", "POST", "PUT"])
    set_widget_id(combo, _COMBO)
    layout.addWidget(combo)

    lst = QListWidget()
    lst.addItems(["Alpha", "Beta", "Gamma"])
    set_widget_id(lst, _LIST)
    layout.addWidget(lst)

    disabled = QPushButton("Nope")
    disabled.setEnabled(False)
    set_widget_id(disabled, _DISABLED)
    layout.addWidget(disabled)

    root.show()
    qapp.processEvents()
    return root, clicks


def _make_tree_fixture(qapp: QApplication) -> QWidget:
    """Isolated tree fixture — avoid QTreeView teardown in every combo/list test."""
    root = QWidget()
    layout = QHBoxLayout(root)
    tree = QTreeView()
    model = QStandardItemModel(tree)
    parent = QStandardItem("Folder")
    parent.appendRow(QStandardItem("Child"))
    model.appendRow(parent)
    model.appendRow(QStandardItem("Sibling"))
    tree.setModel(model)
    set_widget_id(tree, _TREE)
    layout.addWidget(tree)
    root.show()
    qapp.processEvents()
    return root


def _make_list_view_fixture(qapp: QApplication) -> QWidget:
    """Isolated QListView fixture — model-backed, not QListWidget."""
    root = QWidget()
    layout = QHBoxLayout(root)
    view = QListView()
    model = QStandardItemModel(view)
    for label in ("Alpha", "Beta", "Gamma"):
        model.appendRow(QStandardItem(label))
    view.setModel(model)
    set_widget_id(view, _LIST_VIEW)
    layout.addWidget(view)
    root.show()
    qapp.processEvents()
    return root


def test_ui_click_on_fixture(qapp: QApplication) -> None:
    root, clicks = _make_fixture(qapp)
    try:
        assert clicks[0] == 0
        ui_click(root, _BTN)
        assert clicks[0] == 1
    finally:
        root.close()


def test_ui_fill_on_fixture(qapp: QApplication) -> None:
    root, _ = _make_fixture(qapp)
    try:
        ui_fill(root, _INPUT, "https://example.com")
        line = find_widget(root, _INPUT)
        assert isinstance(line, QLineEdit)
        assert line.text() == "https://example.com"
    finally:
        root.close()


def test_ui_fill_via_key_clicks_on_fixture(qapp: QApplication) -> None:
    """PYPOST-917: ui_fill opt-in keyClicks leaves fixture QLineEdit text set."""
    root, _ = _make_fixture(qapp)
    try:
        ui_fill(root, _INPUT, "typed-via-keys", via_key_clicks=True)
        line = find_widget(root, _INPUT)
        assert isinstance(line, QLineEdit)
        assert line.text() == "typed-via-keys"
    finally:
        root.close()


def test_ui_select_on_fixture(qapp: QApplication) -> None:
    root, _ = _make_fixture(qapp)
    try:
        ui_select(root, _COMBO, "POST")
        combo = find_widget(root, _COMBO)
        assert isinstance(combo, QComboBox)
        assert combo.currentText() == "POST"
    finally:
        root.close()


def test_ui_select_list_by_text(qapp: QApplication) -> None:
    """PYPOST-916: ui_select selects a QListWidget row by display text."""
    root, _ = _make_fixture(qapp)
    try:
        ui_select(root, _LIST, "Beta")
        lst = find_widget(root, _LIST)
        assert isinstance(lst, QListWidget)
        assert lst.currentItem() is not None
        assert lst.currentItem().text() == "Beta"
        assert lst.currentRow() == 1
    finally:
        root.close()


def test_ui_select_list_by_index(qapp: QApplication) -> None:
    """PYPOST-916: ui_select selects a QListWidget row by zero-based index."""
    root, _ = _make_fixture(qapp)
    try:
        ui_select(root, _LIST, 0)
        lst = find_widget(root, _LIST)
        assert isinstance(lst, QListWidget)
        assert lst.currentRow() == 0
        assert lst.currentItem() is not None
        assert lst.currentItem().text() == "Alpha"
    finally:
        root.close()


def test_ui_select_list_view_by_text(qapp: QApplication) -> None:
    """PYPOST-939: ui_select selects a QListView row by display text."""
    root = _make_list_view_fixture(qapp)
    try:
        ui_select(root, _LIST_VIEW, "Beta")
        view = find_widget(root, _LIST_VIEW)
        assert isinstance(view, QListView)
        current = view.currentIndex()
        assert current.isValid()
        assert current.data(Qt.ItemDataRole.DisplayRole) == "Beta"
        assert current.row() == 1
    finally:
        close_item_view_fixture(root, qapp, _LIST_VIEW, view_type=QListView)


def test_ui_select_list_view_by_index(qapp: QApplication) -> None:
    """PYPOST-939: ui_select selects a QListView row by zero-based index."""
    root = _make_list_view_fixture(qapp)
    try:
        ui_select(root, _LIST_VIEW, 0)
        view = find_widget(root, _LIST_VIEW)
        assert isinstance(view, QListView)
        current = view.currentIndex()
        assert current.isValid()
        assert current.data(Qt.ItemDataRole.DisplayRole) == "Alpha"
        assert current.row() == 0
    finally:
        close_item_view_fixture(root, qapp, _LIST_VIEW, view_type=QListView)


def test_ui_select_tree_by_text(qapp: QApplication) -> None:
    """PYPOST-916: ui_select selects a nested QTreeView row by display text."""
    root = _make_tree_fixture(qapp)
    try:
        ui_select(root, _TREE, "Child")
        tree = find_widget(root, _TREE)
        assert isinstance(tree, QTreeView)
        current = tree.currentIndex()
        assert current.isValid()
        assert current.data(Qt.ItemDataRole.DisplayRole) == "Child"
    finally:
        close_item_view_fixture(root, qapp, _TREE, view_type=QTreeView)


def test_ui_select_tree_by_index(qapp: QApplication) -> None:
    """PYPOST-916: ui_select selects a top-level QTreeView row by index."""
    root = _make_tree_fixture(qapp)
    try:
        ui_select(root, _TREE, 1)
        tree = find_widget(root, _TREE)
        assert isinstance(tree, QTreeView)
        current = tree.currentIndex()
        assert current.isValid()
        assert current.data(Qt.ItemDataRole.DisplayRole) == "Sibling"
        assert current.row() == 1
        assert not current.parent().isValid()
    finally:
        close_item_view_fixture(root, qapp, _TREE, view_type=QTreeView)


def test_ui_select_combo_by_index(qapp: QApplication) -> None:
    """PYPOST-916: ui_select selects a QComboBox item by zero-based index."""
    root, _ = _make_fixture(qapp)
    try:
        ui_select(root, _COMBO, 2)
        combo = find_widget(root, _COMBO)
        assert isinstance(combo, QComboBox)
        assert combo.currentIndex() == 2
        assert combo.currentText() == "PUT"
    finally:
        root.close()


def test_ui_send_key_on_fixture(qapp: QApplication) -> None:
    root, _ = _make_fixture(qapp)
    try:
        ui_fill(root, _INPUT, "ab")
        ui_send_key(root, _INPUT, "backspace")
        line = find_widget(root, _INPUT)
        assert isinstance(line, QLineEdit)
        assert line.text() == "a"
    finally:
        root.close()


def test_ui_send_key_with_modifier(qapp: QApplication) -> None:
    root, _ = _make_fixture(qapp)
    try:
        ui_fill(root, _INPUT, "hello")
        ui_send_key(
            root,
            _INPUT,
            "a",
            modifiers=Qt.KeyboardModifier.ControlModifier,
        )
        line = find_widget(root, _INPUT)
        assert isinstance(line, QLineEdit)
        # Hotkey delivery must not raise; text remains a string after Ctrl+A.
        assert isinstance(line.text(), str)
    finally:
        root.close()


def test_missing_target_raises(qapp: QApplication) -> None:
    root, _ = _make_fixture(qapp)
    try:
        with pytest.raises(UiTargetNotFoundError) as exc_info:
            ui_click(root, "does_not_exist")
        assert "does_not_exist" in str(exc_info.value)
    finally:
        root.close()


def test_disabled_target_raises(qapp: QApplication) -> None:
    root, _ = _make_fixture(qapp)
    try:
        with pytest.raises(UiTargetNotInteractableError) as exc_info:
            ui_click(root, _DISABLED)
        assert _DISABLED in str(exc_info.value)
        assert "not enabled" in str(exc_info.value)
    finally:
        root.close()


def test_fill_wrong_type_raises(qapp: QApplication) -> None:
    root, _ = _make_fixture(qapp)
    try:
        with pytest.raises(UiTargetNotInteractableError) as exc_info:
            ui_fill(root, _BTN, "nope")
        assert "not a text input" in str(exc_info.value)
    finally:
        root.close()


def test_select_missing_option_raises(qapp: QApplication) -> None:
    root, _ = _make_fixture(qapp)
    try:
        with pytest.raises(UiTargetNotInteractableError) as exc_info:
            ui_select(root, _COMBO, "PATCH")
        assert "option not found" in str(exc_info.value)
    finally:
        root.close()


def test_select_list_missing_option_raises(qapp: QApplication) -> None:
    """PYPOST-942: missing list label raises option not found."""
    root, _ = _make_fixture(qapp)
    try:
        with pytest.raises(UiTargetNotInteractableError) as exc_info:
            ui_select(root, _LIST, "PATCH")
        assert "option not found" in str(exc_info.value)
    finally:
        root.close()


@pytest.mark.parametrize("index", [-1, 3])
def test_select_list_index_out_of_range_raises(
    qapp: QApplication,
    index: int,
) -> None:
    """PYPOST-942: out-of-range list index raises option index out of range."""
    root, _ = _make_fixture(qapp)
    try:
        with pytest.raises(UiTargetNotInteractableError) as exc_info:
            ui_select(root, _LIST, index)
        assert "option index out of range" in str(exc_info.value)
    finally:
        root.close()


def test_select_tree_missing_option_raises(qapp: QApplication) -> None:
    """PYPOST-942: missing tree label raises option not found."""
    root = _make_tree_fixture(qapp)
    try:
        with pytest.raises(UiTargetNotInteractableError) as exc_info:
            ui_select(root, _TREE, "PATCH")
        assert "option not found" in str(exc_info.value)
    finally:
        close_item_view_fixture(root, qapp, _TREE, view_type=QTreeView)


@pytest.mark.parametrize("index", [-1, 2])
def test_select_tree_index_out_of_range_raises(
    qapp: QApplication,
    index: int,
) -> None:
    """PYPOST-942: out-of-range top-level tree index raises option index out of range."""
    root = _make_tree_fixture(qapp)
    try:
        with pytest.raises(UiTargetNotInteractableError) as exc_info:
            ui_select(root, _TREE, index)
        assert "option index out of range" in str(exc_info.value)
    finally:
        close_item_view_fixture(root, qapp, _TREE, view_type=QTreeView)


def test_main_window_fill_url_and_select_method(
    agent_e2e_session: AgentAppSession,
) -> None:
    session = agent_e2e_session
    assert session.window.is_ui_ready
    session.ui_fill(URL_INPUT, "https://httpbin.org/get")
    url = find_widget(session.window, URL_INPUT)
    assert isinstance(url, QLineEdit)
    assert url.text() == "https://httpbin.org/get"

    session.ui_select(METHOD_COMBO, "POST")
    method = find_widget(session.window, METHOD_COMBO)
    assert isinstance(method, QComboBox)
    assert method.currentText() == "POST"


def test_ui_fill_via_key_clicks_session(
    agent_e2e_session: AgentAppSession,
) -> None:
    """PYPOST-917: session.ui_fill accepts via_key_clicks and fills URL field."""
    session = agent_e2e_session
    assert session.window.is_ui_ready
    session.ui_fill(
        URL_INPUT,
        "https://typed-via-keys.example/",
        via_key_clicks=True,
    )
    url = find_widget(session.window, URL_INPUT)
    assert isinstance(url, QLineEdit)
    assert url.text() == "https://typed-via-keys.example/"


def test_current_tab_scoped_fill(agent_e2e_session: AgentAppSession) -> None:
    """PYPOST-851: in_current_tab resolves per-tab role ids under active tab."""
    session = agent_e2e_session
    assert session.window.is_ui_ready
    tab = session.current_request_tab()
    assert tab is session.window.tabs.widget.currentWidget()
    session.ui_fill(URL_INPUT, "https://scoped.example/", in_current_tab=True)
    url = session.find_in_current_tab(URL_INPUT)
    assert isinstance(url, QLineEdit)
    assert url.text() == "https://scoped.example/"


def test_ui_action_applied_caplog(qapp: QApplication, caplog: pytest.LogCaptureFixture) -> None:
    """PYPOST-851: ui_action_applied DEBUG scalars; fill text never logged."""
    import logging

    root, _ = _make_fixture(qapp)
    try:
        secret = "must-not-appear-in-logs"
        with caplog.at_level(logging.DEBUG, logger="pypost.agent.ui_actions"):
            ui_fill(root, _INPUT, secret)
        records = [
            r
            for r in caplog.records
            if r.name == "pypost.agent.ui_actions" and "ui_action_applied" in r.message
        ]
        assert records
        msg = records[-1].getMessage()
        assert "primitive=fill" in msg
        assert f"widget_id={_INPUT}" in msg
        assert "outcome=ok" in msg
        assert "duration_ms=" in msg
        assert "via_key_clicks=false" in msg
        assert secret not in msg
        assert secret not in caplog.text
    finally:
        root.close()
