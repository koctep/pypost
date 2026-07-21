"""PYPOST-835: UI state snapshot shape, masking, and ready integration."""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import (
    QApplication,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pypost.agent.lifecycle import AgentAppSession
from pypost.agent.ui_snapshot import (
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

pytestmark = pytest.mark.timeout(60)

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
    """Unit: long text values are truncated to UI_SNAPSHOT_MAX_VALUE_LENGTH."""
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


def test_ui_snapshot_after_ready_includes_key_surfaces(qapp: QApplication) -> None:
    """Integration: after ready, snapshot includes key pypost_* names."""
    assert QApplication.instance() is qapp

    with AgentAppSession(offscreen=True, ready_timeout=30.0) as session:
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
