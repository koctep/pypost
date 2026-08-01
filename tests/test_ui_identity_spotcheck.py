"""PYPOST-834: spot-check — key widgets expose stable objectName identities."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QLabel,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QTreeView,
    QWidget,
)

from pypost.agent.lifecycle import AgentAppSession
from pypost.ui.presenters.tabs_presenter import RequestTab
from pypost.ui.widget_ids import (
    COLLECTION_TREE,
    ENV_BAR,
    ENV_MANAGE_BUTTON,
    ENV_SELECTOR,
    MAIN_WINDOW,
    METHOD_COMBO,
    REQUEST_BODY_EDIT,
    REQUEST_DETAIL_TABS,
    REQUEST_TABS,
    RESPONSE_BODY,
    RESPONSE_PANEL,
    RESPONSE_STATUS,
    SEND_BUTTON,
    SETTINGS_BUTTON,
    URL_INPUT,
)
from pypost.ui.widgets.code_editor import CodeEditor
from pypost.ui.widgets.request_editor import RequestWidget
from pypost.ui.widgets.response_view import ResponseView

pytestmark = [
    pytest.mark.timeout(60),
    pytest.mark.agent_e2e,
]


def _assert_id(widget: QObject, expected: str) -> None:
    assert widget.objectName() == expected
    if isinstance(widget, QWidget):
        getter = getattr(widget, "accessibleIdentifier", None)
        if callable(getter):
            assert getter() == expected


def _assert_key_identities(window: QWidget) -> None:
    """Assert documented key objectNames (and accessibleIdentifier mirrors)."""
    _assert_id(window, MAIN_WINDOW)

    tree = window.findChild(QTreeView, COLLECTION_TREE)
    assert tree is not None
    _assert_id(tree, COLLECTION_TREE)
    assert tree is window.collections.widget

    tabs = window.findChild(QTabWidget, REQUEST_TABS)
    assert tabs is not None
    _assert_id(tabs, REQUEST_TABS)
    assert tabs is window.tabs.widget

    settings_btn = window.findChild(QPushButton, SETTINGS_BUTTON)
    assert settings_btn is not None
    _assert_id(settings_btn, SETTINGS_BUTTON)

    env_bar = window.findChild(QWidget, ENV_BAR)
    assert env_bar is not None
    _assert_id(env_bar, ENV_BAR)
    assert env_bar is window.env.widget

    env_selector = window.findChild(QComboBox, ENV_SELECTOR)
    assert env_selector is not None
    _assert_id(env_selector, ENV_SELECTOR)

    env_manage = window.findChild(QPushButton, ENV_MANAGE_BUTTON)
    assert env_manage is not None
    _assert_id(env_manage, ENV_MANAGE_BUTTON)

    current = tabs.currentWidget()
    assert isinstance(current, RequestTab)

    method = current.findChild(QComboBox, METHOD_COMBO)
    assert method is not None
    _assert_id(method, METHOD_COMBO)

    url = current.findChild(QWidget, URL_INPUT)
    assert url is not None
    _assert_id(url, URL_INPUT)

    send = current.findChild(QPushButton, SEND_BUTTON)
    assert send is not None
    _assert_id(send, SEND_BUTTON)

    detail_tabs = current.findChild(QTabWidget, REQUEST_DETAIL_TABS)
    assert detail_tabs is not None
    _assert_id(detail_tabs, REQUEST_DETAIL_TABS)

    body = current.findChild(CodeEditor, REQUEST_BODY_EDIT)
    assert body is not None
    _assert_id(body, REQUEST_BODY_EDIT)

    response = current.findChild(ResponseView, RESPONSE_PANEL)
    assert response is not None
    _assert_id(response, RESPONSE_PANEL)

    status = response.findChild(QLabel, RESPONSE_STATUS)
    assert status is not None
    _assert_id(status, RESPONSE_STATUS)

    response_body = response.findChild(QTextEdit, RESPONSE_BODY)
    assert response_body is not None
    _assert_id(response_body, RESPONSE_BODY)

    assert isinstance(current.request_editor, RequestWidget)
    assert current.request_editor.send_btn is send
    assert current.request_editor.body_edit is body
    assert current.response_view is response


def test_key_widgets_expose_stable_identities(
    qapp: QApplication,
    agent_e2e_session: AgentAppSession,
) -> None:
    """FR10: after UI ready, critical surfaces expose documented objectNames."""
    assert QApplication.instance() is qapp
    window = agent_e2e_session.window
    assert window.is_ui_ready is True
    _assert_key_identities(window)


def test_theme_apply_keeps_key_object_names(
    qapp: QApplication,
    agent_e2e_session: AgentAppSession,
) -> None:
    """Theme/apply_settings must not clear key objectNames (PYPOST-844)."""
    window = agent_e2e_session.window
    assert window.is_ui_ready is True
    _assert_key_identities(window)

    flipped = "dark" if window.settings.theme != "dark" else "light"
    window.apply_settings(window.settings.model_copy(update={"theme": flipped}))
    qapp.processEvents()
    _assert_key_identities(window)


def test_second_request_tab_exposes_role_object_names(
    qapp: QApplication,
    agent_e2e_session: AgentAppSession,
) -> None:
    """Multi-tab: role ids exist on a newly added request tab (PYPOST-846)."""
    window = agent_e2e_session.window
    assert window.is_ui_ready is True
    window.tabs.add_new_tab(save_state=False)
    qapp.processEvents()

    tabs = window.findChild(QTabWidget, REQUEST_TABS)
    assert tabs is not None
    second = tabs.currentWidget()
    assert isinstance(second, RequestTab)

    for expected, cls in (
        (METHOD_COMBO, QComboBox),
        (URL_INPUT, QWidget),
        (SEND_BUTTON, QPushButton),
        (REQUEST_BODY_EDIT, CodeEditor),
        (RESPONSE_PANEL, ResponseView),
    ):
        widget = second.findChild(cls, expected)
        assert widget is not None, expected
        _assert_id(widget, expected)

    response = second.findChild(ResponseView, RESPONSE_PANEL)
    assert response is not None
    status = response.findChild(QLabel, RESPONSE_STATUS)
    assert status is not None, RESPONSE_STATUS
    _assert_id(status, RESPONSE_STATUS)
    response_body = response.findChild(QTextEdit, RESPONSE_BODY)
    assert response_body is not None, RESPONSE_BODY
    _assert_id(response_body, RESPONSE_BODY)


def test_widget_ids_are_locale_independent_literals() -> None:
    """FR9: key ids are fixed ASCII constants, not derived from UI text."""
    from pypost.ui import widget_ids

    for name in widget_ids.KEY_WIDGET_IDS:
        assert name.startswith("pypost_")
        assert name.isascii()
        assert " " not in name
        assert name == name.lower()
