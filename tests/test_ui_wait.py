"""PYPOST-837: Settle/wait helpers — async fixture + session integration."""

from __future__ import annotations

import json

import pytest
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)

from pypost.agent.lifecycle import AgentAppSession
from pypost.agent.ui_actions import ui_fill
from pypost.fixtures.agent_e2e_http import (
    CANNED_GOLDEN_OK,
    GOLDEN_BODY,
    GOLDEN_METHOD,
    GOLDEN_STATUS,
    GOLDEN_URL,
    stub_agent_e2e_http,
)
from pypost.agent.ui_wait import (
    UiWaitTimeoutError,
    wait_for_enabled,
    wait_for_snapshot,
    wait_for_text,
    wait_for_widget,
    wait_until,
)
from pypost.ui.presenters.tabs_presenter import RequestTab
from pypost.ui.widget_ids import (
    METHOD_COMBO,
    RESPONSE_BODY,
    RESPONSE_STATUS,
    SEND_BUTTON,
    URL_INPUT,
    set_widget_id,
)

pytestmark = [
    pytest.mark.timeout(60),
    pytest.mark.agent_e2e,
]

_DELAYED = "fixture_delayed_widget"
_DISABLED = "fixture_delayed_enabled"
_LABEL = "fixture_delayed_label"
_INPUT = "fixture_async_input"


def _make_root(qapp: QApplication) -> QWidget:
    root = QWidget()
    root.setLayout(QHBoxLayout())
    root.show()
    qapp.processEvents()
    return root


def test_wait_for_widget_after_delayed_create(qapp: QApplication) -> None:
    root = _make_root(qapp)
    try:

        def _create() -> None:
            btn = QPushButton("Later")
            set_widget_id(btn, _DELAYED)
            root.layout().addWidget(btn)

        QTimer.singleShot(80, _create)
        widget = wait_for_widget(root, _DELAYED, timeout=2.0)
        assert widget.objectName() == _DELAYED
    finally:
        root.close()


def test_wait_for_enabled_after_delayed_enable(qapp: QApplication) -> None:
    root = _make_root(qapp)
    try:
        btn = QPushButton("Soon")
        btn.setEnabled(False)
        set_widget_id(btn, _DISABLED)
        root.layout().addWidget(btn)
        qapp.processEvents()

        QTimer.singleShot(80, lambda: btn.setEnabled(True))
        resolved = wait_for_enabled(root, _DISABLED, timeout=2.0)
        assert resolved is btn
        assert btn.isEnabled()
    finally:
        root.close()


def test_wait_for_text_after_delayed_update(qapp: QApplication) -> None:
    root = _make_root(qapp)
    try:
        label = QLabel("pending")
        set_widget_id(label, _LABEL)
        root.layout().addWidget(label)
        qapp.processEvents()

        QTimer.singleShot(80, lambda: label.setText("ready"))
        resolved = wait_for_text(root, _LABEL, "ready", timeout=2.0)
        assert resolved.text() == "ready"

        QTimer.singleShot(80, lambda: label.setText("done-ok"))
        wait_for_text(root, _LABEL, lambda t: t.startswith("done"), timeout=2.0)
    finally:
        root.close()


def test_wait_for_snapshot_predicate(qapp: QApplication) -> None:
    root = _make_root(qapp)
    try:
        line = QLineEdit("before")
        set_widget_id(line, _INPUT)
        root.layout().addWidget(line)
        qapp.processEvents()

        def _flip() -> None:
            line.setText("settled")

        QTimer.singleShot(80, _flip)

        def _pred(snap: dict) -> bool:
            def _walk(node: dict) -> bool:
                if node.get("name") == _INPUT and node.get("value") == "settled":
                    return True
                return any(
                    _walk(child)
                    for child in node.get("children") or []
                    if isinstance(child, dict)
                )

            return _walk(snap)

        snap = wait_for_snapshot(root, _pred, timeout=2.0)
        assert snap.get("role")
    finally:
        root.close()


def test_wait_until_timeout_diagnostics(qapp: QApplication) -> None:
    root = _make_root(qapp)
    try:
        with pytest.raises(UiWaitTimeoutError) as exc_info:
            wait_until(
                lambda: False,
                timeout=0.15,
                interval=0.05,
                message="never",
                condition_name="always_false",
                diagnostics_factory=lambda: {"probe": "x"},
            )
        err = exc_info.value
        assert err.condition == "always_false"
        assert err.timeout_s == 0.15
        assert err.diagnostics.get("probe") == "x"
        assert "never" in str(err)
    finally:
        root.close()


def test_wait_for_widget_timeout_includes_widget_id(qapp: QApplication) -> None:
    root = _make_root(qapp)
    try:
        with pytest.raises(UiWaitTimeoutError) as exc_info:
            wait_for_widget(root, "missing_id", timeout=0.15)
        assert exc_info.value.diagnostics.get("widget_id") == "missing_id"
        assert "missing_id" in str(exc_info.value)
    finally:
        root.close()


def test_session_wait_for_text_in_current_tab_after_multi_tab_send(
    qapp: QApplication,
    agent_e2e_session: AgentAppSession,
) -> None:
    """PYPOST-949: tab-scoped session text wait targets active tab after Send."""
    session = agent_e2e_session
    assert session.window.is_ui_ready

    first_tab = session.current_request_tab()
    assert isinstance(first_tab, RequestTab)

    session.window.tabs.add_new_tab(save_state=False)
    qapp.processEvents()
    second_tab = session.current_request_tab()
    assert second_tab is not first_tab

    status_label = f"Status: {GOLDEN_STATUS}"
    body_display = json.dumps(json.loads(GOLDEN_BODY), indent=2)

    session.ui_fill(URL_INPUT, GOLDEN_URL, in_current_tab=True)
    session.ui_select(METHOD_COMBO, GOLDEN_METHOD, in_current_tab=True)

    with stub_agent_e2e_http(CANNED_GOLDEN_OK):
        session.ui_click(SEND_BUTTON, in_current_tab=True)

        with pytest.raises(UiWaitTimeoutError):
            session.wait_for_text(RESPONSE_STATUS, status_label, timeout=0.5)

        status_widget = session.wait_for_text(
            RESPONSE_STATUS,
            status_label,
            in_current_tab=True,
            timeout=5.0,
        )
        assert status_widget.objectName() == RESPONSE_STATUS
        body_widget = session.wait_for_text(
            RESPONSE_BODY,
            body_display,
            in_current_tab=True,
            timeout=5.0,
        )
        assert body_widget.objectName() == RESPONSE_BODY


def test_session_wait_for_text_after_fill(
    agent_e2e_session: AgentAppSession,
) -> None:
    session = agent_e2e_session
    session.ui_fill(URL_INPUT, "https://wait.example")
    widget = session.wait_for_text(URL_INPUT, "https://wait.example", timeout=5.0)
    assert isinstance(widget, QLineEdit)
    assert widget.text() == "https://wait.example"


def test_session_wait_for_enabled_send_path(
    agent_e2e_session: AgentAppSession,
) -> None:
    """After fill, wait until URL input stays enabled (post-action settle)."""
    session = agent_e2e_session
    ui_fill(session.window, URL_INPUT, "https://settle.example")
    enabled = session.wait_for_enabled(URL_INPUT, timeout=5.0)
    assert enabled.isEnabled()
    session.wait_for_snapshot(
        lambda snap: _snapshot_has_name(snap, URL_INPUT),
        timeout=5.0,
    )


def test_wait_for_text_fast_fails_without_text_api(qapp: QApplication) -> None:
    """PYPOST-852: no-text-API widgets fail immediately (no full timeout)."""
    root = _make_root(qapp)
    try:
        plain = QWidget()
        set_widget_id(plain, "fixture_no_text")
        root.layout().addWidget(plain)
        qapp.processEvents()
        with pytest.raises(UiWaitTimeoutError) as exc_info:
            wait_for_text(root, "fixture_no_text", "anything", timeout=5.0)
        assert exc_info.value.condition == "no_text_api"
        assert exc_info.value.timeout_s == 0.0
    finally:
        root.close()


def _snapshot_has_name(node: dict, name: str) -> bool:
    if node.get("name") == name:
        return True
    return any(
        _snapshot_has_name(child, name)
        for child in node.get("children") or []
        if isinstance(child, dict)
    )
