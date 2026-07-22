"""PYPOST-835: UI state snapshot shape, masking, and ready integration."""

from __future__ import annotations

import logging

import pytest
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QLineEdit,
    QListView,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from pypost.agent.lifecycle import AgentAppSession
from pypost.agent.ui_snapshot import (
    UI_SNAPSHOT_ITEM_VIEW_SELECTION_CAP,
    UI_SNAPSHOT_MAX_VALUE_LENGTH,
    capture_ui_snapshot,
)
from pypost.core.sensitive_text_sanitizer import HIDDEN_PLACEHOLDER
from pypost.ui.widget_ids import (
    COLLECTION_TREE,
    MAIN_WINDOW,
    REQUEST_TABS,
    SEND_BUTTON,
    URL_INPUT,
)

pytestmark = [
    pytest.mark.timeout(60),
    pytest.mark.agent_e2e,
]

_NODE_KEYS = frozenset({"role", "name", "value", "children"})


class _FakeEnv:
    def __init__(
        self,
        variables: dict[str, str] | None = None,
        hidden_keys: set[str] | None = None,
    ) -> None:
        self._variables = dict(variables or {})
        self._hidden_keys = set(hidden_keys or ())

    @property
    def current_variables(self) -> dict[str, str]:
        return dict(self._variables)

    @property
    def current_hidden_keys(self) -> set[str]:
        return set(self._hidden_keys)


def _assert_node_shape(node: dict) -> None:
    assert set(node.keys()) == _NODE_KEYS
    assert isinstance(node["role"], str)
    assert isinstance(node["name"], str)
    assert node["value"] is None or isinstance(node["value"], str)
    assert isinstance(node["children"], list)
    for child in node["children"]:
        _assert_node_shape(child)


def _find_names(node: dict) -> set[str]:
    names: set[str] = set()
    if node["name"]:
        names.add(node["name"])
    for child in node["children"]:
        names.update(_find_names(child))
    return names


def _find_by_name(node: dict, name: str) -> dict | None:
    if node["name"] == name:
        return node
    for child in node["children"]:
        found = _find_by_name(child, name)
        if found is not None:
            return found
    return None


def test_capture_ui_snapshot_shape_and_hierarchy(qapp: QApplication) -> None:
    """Unit: snapshot nodes have role/name/value/children hierarchy."""
    assert QApplication.instance() is qapp

    root = QWidget()
    root.setObjectName("test_root")
    layout = QVBoxLayout(root)
    button = QPushButton("Go")
    button.setObjectName("test_button")
    edit = QLineEdit("hello")
    edit.setObjectName("test_edit")
    layout.addWidget(button)
    layout.addWidget(edit)
    root.show()
    qapp.processEvents()

    snap = capture_ui_snapshot(root)
    _assert_node_shape(snap)
    assert snap["role"] == "widget"
    assert snap["name"] == "test_root"
    names = _find_names(snap)
    assert "test_button" in names
    assert "test_edit" in names

    btn_node = _find_by_name(snap, "test_button")
    assert btn_node is not None
    assert btn_node["role"] == "button"
    assert btn_node["value"] == "Go"

    edit_node = _find_by_name(snap, "test_edit")
    assert edit_node is not None
    assert edit_node["role"] == "line_edit"
    assert edit_node["value"] == "hello"


def test_capture_ui_snapshot_masks_hidden_env_values(qapp: QApplication) -> None:
    """Unit: hidden env values are redacted via sanitize_text."""
    assert QApplication.instance() is qapp

    secret = "super-secret-token-xyz"
    root = QWidget()
    root.env = _FakeEnv(  # type: ignore[attr-defined]
        variables={"api_key": secret},
        hidden_keys={"api_key"},
    )
    layout = QVBoxLayout(root)
    edit = QLineEdit(f"Authorization: Bearer {secret}")
    edit.setObjectName("secret_edit")
    layout.addWidget(edit)
    root.show()
    qapp.processEvents()

    snap = capture_ui_snapshot(root)
    node = _find_by_name(snap, "secret_edit")
    assert node is not None
    assert secret not in (node["value"] or "")
    assert HIDDEN_PLACEHOLDER in (node["value"] or "")


def test_capture_ui_snapshot_truncates_long_values(qapp: QApplication) -> None:
    """Unit: long text values are truncated with an ellipsis (PYPOST-849)."""
    assert QApplication.instance() is qapp

    root = QWidget()
    layout = QVBoxLayout(root)
    edit = QLineEdit("x" * (UI_SNAPSHOT_MAX_VALUE_LENGTH + 50))
    edit.setObjectName("long_edit")
    layout.addWidget(edit)
    root.show()
    qapp.processEvents()

    snap = capture_ui_snapshot(root)
    node = _find_by_name(snap, "long_edit")
    assert node is not None
    assert node["value"] is not None
    assert len(node["value"]) == UI_SNAPSHOT_MAX_VALUE_LENGTH
    assert node["value"].endswith("…")
    assert node["value"][:-1] == "x" * (UI_SNAPSHOT_MAX_VALUE_LENGTH - 1)


def test_ui_snapshot_after_ready_includes_key_surfaces(
    qapp: QApplication,
    agent_e2e_session: AgentAppSession,
) -> None:
    """Integration: after ready, snapshot includes key pypost_* names."""
    assert QApplication.instance() is qapp

    session = agent_e2e_session
    assert session.window.is_ui_ready is True
    snap = session.ui_snapshot()
    _assert_node_shape(snap)
    assert snap["role"] == "window"
    assert snap["name"] == MAIN_WINDOW

    names = _find_names(snap)
    for expected in (
        MAIN_WINDOW,
        COLLECTION_TREE,
        REQUEST_TABS,
        URL_INPUT,
        SEND_BUTTON,
    ):
        assert expected in names, f"missing {expected} in snapshot"


def test_capture_skips_invisible_and_prunes_unnamed_chrome(
    qapp: QApplication,
) -> None:
    """Invisible widgets are omitted; empty unnamed chrome is pruned."""
    root = QWidget()
    root.setObjectName("prune_root")
    layout = QVBoxLayout(root)
    visible = QPushButton("Visible")
    visible.setObjectName("visible_btn")
    hidden = QPushButton("Hidden")
    hidden.setObjectName("hidden_btn")
    chrome = QWidget()  # unnamed, no value → prune when empty
    layout.addWidget(visible)
    layout.addWidget(hidden)
    layout.addWidget(chrome)
    root.show()
    hidden.hide()
    qapp.processEvents()

    snap = capture_ui_snapshot(root)
    names = _find_names(snap)
    assert "visible_btn" in names
    assert "hidden_btn" not in names
    assert "" not in names or snap["name"] == "prune_root"


def test_capture_tab_combo_and_item_view_values(qapp: QApplication) -> None:
    """Tab title, combo current text, and item-view selection extractors."""
    root = QWidget()
    root.setObjectName("extractor_root")
    layout = QVBoxLayout(root)

    tabs = QTabWidget()
    tabs.setObjectName("test_tabs")
    tabs.addTab(QWidget(), "Alpha")
    tabs.addTab(QWidget(), "Beta")
    tabs.setCurrentIndex(1)

    combo = QComboBox()
    combo.setObjectName("test_combo")
    combo.addItems(["one", "two", "three"])
    combo.setCurrentIndex(2)

    model = QStandardItemModel()
    for label in ("a", "b", "c", "d", "e", "f"):
        model.appendRow(QStandardItem(label))
    view = QListView()
    view.setObjectName("test_list")
    view.setModel(model)
    view.setSelectionMode(QListView.SelectionMode.MultiSelection)
    for row in range(model.rowCount()):
        view.selectionModel().select(
            model.index(row, 0),
            view.selectionModel().SelectionFlag.Select,
        )

    layout.addWidget(tabs)
    layout.addWidget(combo)
    layout.addWidget(view)
    root.show()
    qapp.processEvents()

    snap = capture_ui_snapshot(root)
    tab_node = _find_by_name(snap, "test_tabs")
    assert tab_node is not None
    assert tab_node["role"] == "tab_widget"
    assert tab_node["value"] == "Beta"

    combo_node = _find_by_name(snap, "test_combo")
    assert combo_node is not None
    assert combo_node["role"] == "combo_box"
    assert combo_node["value"] == "three"

    list_node = _find_by_name(snap, "test_list")
    assert list_node is not None
    assert list_node["role"] == "item_view"
    parts = (list_node["value"] or "").split(", ")
    assert len(parts) == UI_SNAPSHOT_ITEM_VIEW_SELECTION_CAP
    assert parts == ["a", "b", "c", "d", "e"]


def test_capture_logs_ui_snapshot_captured_scalars(
    qapp: QApplication,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """DEBUG ui_snapshot_captured includes node_count, named_count, duration_ms."""
    root = QWidget()
    root.setObjectName("log_root")
    layout = QVBoxLayout(root)
    btn = QPushButton("Go")
    btn.setObjectName("log_btn")
    layout.addWidget(btn)
    root.show()
    qapp.processEvents()

    with caplog.at_level(logging.DEBUG, logger="pypost.agent.ui_snapshot"):
        capture_ui_snapshot(root)

    matching = [
        r
        for r in caplog.records
        if r.name == "pypost.agent.ui_snapshot" and "ui_snapshot_captured" in r.message
    ]
    assert matching, "expected ui_snapshot_captured DEBUG log"
    msg = matching[-1].getMessage()
    assert "node_count=" in msg
    assert "named_count=" in msg
    assert "duration_ms=" in msg


def test_ui_snapshot_before_start_raises() -> None:
    """session.ui_snapshot() before start raises like other session accessors."""
    session = AgentAppSession(offscreen=True)
    with pytest.raises(RuntimeError, match="has not been started"):
        session.ui_snapshot()
