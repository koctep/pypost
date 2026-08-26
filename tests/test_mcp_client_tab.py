"""PYPOST-1166: MCP Client draft-shell chrome (no live MCP)."""

from __future__ import annotations

import logging

import pytest
from PySide6.QtWidgets import (
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidgetItem,
    QWidget,
)

from pypost.models.mcp_client import McpClientConnection
from pypost.ui import widget_ids
from pypost.ui.presenters.mcp_client_presenter import McpClientPresenter
from pypost.ui.widget_ids import (
    MCP_CLIENT_HEADERS_TABLE,
    MCP_CLIENT_TAB_PAGE,
    METHOD_COMBO,
)
from pypost.ui.widgets.mcp_client.mcp_client_tab import McpClientTab

pytestmark = pytest.mark.timeout(30)


def _build_draft_tab() -> McpClientTab:
    """Construct a blank MCP Client draft tab with a local presenter."""
    connection = McpClientConnection()
    presenter = McpClientPresenter(connection)
    return McpClientTab(connection, presenter)


def _visible_button_labels(tab: QWidget) -> set[str]:
    return {
        button.text().replace("&", "")
        for button in tab.findChildren(QPushButton)
    }


def _widget_text(widget: QWidget) -> str:
    parts: list[str] = []
    text_fn = getattr(widget, "text", None)
    if callable(text_fn):
        parts.append(str(text_fn()))
    for label in widget.findChildren(QLabel):
        parts.append(label.text())
    return " ".join(parts)


def _tool_item_count(tools: QWidget) -> int:
    count_fn = getattr(tools, "count", None)
    if callable(count_fn):
        try:
            return int(count_fn())
        except TypeError:
            pass
    model_fn = getattr(tools, "model", None)
    if callable(model_fn):
        model = model_fn()
        if model is not None:
            return int(model.rowCount())
    raise AssertionError(
        "MCP Client tool browser must be an empty list or view, "
        f"got {type(tools).__name__}"
    )


def test_draft_shell_has_url_connect_disconnect_state_and_empty_tools(
    qapp,
) -> None:
    tab = _build_draft_tab()
    assert tab.objectName() == MCP_CLIENT_TAB_PAGE
    assert tab.findChild(QWidget, METHOD_COMBO) is None

    url = tab.findChild(QLineEdit, widget_ids.MCP_CLIENT_URL_INPUT) or (
        tab.findChild(QWidget, widget_ids.MCP_CLIENT_URL_INPUT)
    )
    assert url is not None, "draft shell must include an empty URL field"
    text_fn = getattr(url, "text", None)
    assert callable(text_fn)
    assert text_fn() == ""

    connect_btn = tab.findChild(
        QPushButton,
        widget_ids.MCP_CLIENT_CONNECT_BUTTON,
    )
    disconnect_btn = tab.findChild(
        QPushButton,
        widget_ids.MCP_CLIENT_DISCONNECT_BUTTON,
    )
    assert connect_btn is not None
    assert disconnect_btn is not None
    labels = _visible_button_labels(tab)
    assert "Connect" in labels
    assert "Disconnect" in labels

    state = tab.findChild(QWidget, widget_ids.MCP_CLIENT_STATE_BADGE)
    assert state is not None
    state_text = _widget_text(state).strip().lower()
    assert any(
        token in state_text for token in ("disconnected", "idle")
    ), state_text
    assert state_text.replace("disconnected", "").strip() != "connected"

    tools = tab.findChild(QWidget, widget_ids.MCP_CLIENT_TOOL_BROWSER)
    assert tools is not None
    assert _tool_item_count(tools) == 0

    assert widget_ids.MCP_CLIENT_URL_INPUT == "pypost_mcp_client_url_input"
    assert (
        widget_ids.MCP_CLIENT_CONNECT_BUTTON
        == "pypost_mcp_client_connect_button"
    )
    assert (
        widget_ids.MCP_CLIENT_DISCONNECT_BUTTON
        == "pypost_mcp_client_disconnect_button"
    )
    assert widget_ids.MCP_CLIENT_STATE_BADGE == "pypost_mcp_client_state_badge"
    assert (
        widget_ids.MCP_CLIENT_TOOL_BROWSER == "pypost_mcp_client_tool_browser"
    )


def test_mcp_client_tab_has_headers_table(qapp) -> None:
    """FR-1: MCP Client draft chrome includes an editable Headers table."""
    tab = _build_draft_tab()
    assert tab.objectName() == MCP_CLIENT_TAB_PAGE
    assert tab.findChild(QWidget, METHOD_COMBO) is None

    headers_id = MCP_CLIENT_HEADERS_TABLE
    assert headers_id == "pypost_mcp_client_headers_table"
    table = tab.findChild(QWidget, headers_id)
    assert table is not None, (
        "MCP Client draft must include a Headers table "
        f"with id {headers_id}"
    )

    label_text = " ".join(
        label.text() for label in tab.findChildren(QLabel)
    ).lower()
    assert "headers" in label_text, (
        "MCP Client draft must show a user-visible Headers label"
    )

    get_data = getattr(table, "get_data", None)
    assert callable(get_data)
    last = table.rowCount() - 1
    assert last >= 0
    table.setItem(last, 0, QTableWidgetItem("Authorization"))
    table.setItem(last, 1, QTableWidgetItem("Bearer {{token}}"))
    assert table.rowCount() == last + 2
    assert get_data()["Authorization"] == "Bearer {{token}}"

    table.setItem(0, 0, QTableWidgetItem(""))
    table.setItem(0, 1, QTableWidgetItem(""))
    assert "Authorization" not in get_data()

    tools = tab.findChild(QWidget, widget_ids.MCP_CLIENT_TOOL_BROWSER)
    assert tools is not None
    assert _tool_item_count(tools) == 0


def test_presenter_logs_connect_disconnect_teardown(caplog, qapp) -> None:
    """Local chrome lifecycle emits INFO events without URL or payload dumps."""
    tab = _build_draft_tab()
    presenter = tab.presenter
    logger_name = "pypost.ui.presenters.mcp_client_presenter"
    with caplog.at_level(logging.INFO, logger=logger_name):
        presenter.connect_requested()
        presenter.disconnect_requested()
        presenter.teardown()
    messages = [
        record.getMessage()
        for record in caplog.records
        if record.name == logger_name
    ]
    connection_id = tab.connection_data.id
    assert any(
        "mcp_client_connect_initiated" in msg
        and f"connection_id={connection_id}" in msg
        for msg in messages
    )
    assert any(
        "mcp_client_disconnect_initiated" in msg
        and f"connection_id={connection_id}" in msg
        for msg in messages
    )
    assert any(
        "mcp_client_presenter_teardown" in msg
        and f"connection_id={connection_id}" in msg
        for msg in messages
    )
    joined = " ".join(messages)
    assert "http://" not in joined
    assert "headers" not in joined.lower()
