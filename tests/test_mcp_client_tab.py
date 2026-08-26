"""MCP Client draft-shell chrome and live Connect/list_tools (PYPOST-1169)."""

from __future__ import annotations

import json
import logging
from typing import Any
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QTableWidgetItem,
    QWidget,
)

from pypost.models.errors import ErrorCategory, ExecutionError
from pypost.models.mcp_client import McpClientConnection
from pypost.models.response import ResponseData
from pypost.ui import widget_ids
from pypost.ui.presenters.mcp_client_presenter import McpClientPresenter
from pypost.ui.widget_ids import (
    MCP_CLIENT_ERROR_LABEL,
    MCP_CLIENT_HEADERS_TABLE,
    MCP_CLIENT_REFRESH_BUTTON,
    MCP_CLIENT_TAB_PAGE,
    METHOD_COMBO,
)
from pypost.ui.widgets.mcp_client.mcp_client_tab import McpClientTab
from tests.helpers.qt_wait import wait_until

pytestmark = pytest.mark.timeout(30)

_MCP_URL = "http://127.0.0.1:1080/mcp"
_CONNECT_SETTLE_S = 5.0


def _build_draft_tab(
    *,
    mcp_client: Any | None = None,
    env_vars: dict[str, str] | None = None,
    hidden_keys: set[str] | None = None,
    url: str = "",
    headers: dict[str, str] | None = None,
    metrics: Any | None = None,
) -> McpClientTab:
    """Construct an MCP Client draft tab with optional mocked outbound client."""
    connection = McpClientConnection(url=url, headers=dict(headers or {}))
    presenter = McpClientPresenter(
        connection,
        env_vars=env_vars,
        hidden_keys=hidden_keys,
        mcp_client=mcp_client,
        metrics=metrics,
    )
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


def _tools_response(
    tools: list[dict[str, str]] | None = None,
) -> ResponseData:
    if tools is None:
        tools = [{"name": "echo", "description": "Echo tool"}]
    payload = json.dumps({"tools": tools})
    return ResponseData(
        status_code=200,
        headers={},
        body=payload,
        elapsed_time=0.01,
        size=len(payload),
    )


def _set_url(tab: McpClientTab, url: str) -> None:
    field = tab.findChild(QLineEdit, widget_ids.MCP_CLIENT_URL_INPUT)
    assert field is not None
    field.setText(url)


def _click_connect(tab: McpClientTab) -> None:
    button = tab.findChild(QPushButton, widget_ids.MCP_CLIENT_CONNECT_BUTTON)
    assert button is not None
    button.click()


def _refresh_button(tab: QWidget) -> QPushButton | None:
    return tab.findChild(QPushButton, MCP_CLIENT_REFRESH_BUTTON)


def _error_text(tab: QWidget) -> str:
    error = tab.findChild(QWidget, MCP_CLIENT_ERROR_LABEL)
    if error is None:
        return ""
    return _widget_text(error).strip()


def _state_text(tab: QWidget) -> str:
    state = tab.findChild(QWidget, widget_ids.MCP_CLIENT_STATE_BADGE)
    assert state is not None
    return _widget_text(state).strip().lower()


def _is_connected_badge(tab: QWidget) -> bool:
    text = _state_text(tab)
    return (
        "connected" in text
        and "disconnected" not in text
        and "connecting" not in text
        and "failed" not in text
    )


def _is_failed_or_disconnected_badge(tab: QWidget) -> bool:
    text = _state_text(tab)
    if _is_connected_badge(tab):
        return False
    return any(
        token in text
        for token in ("disconnected", "idle", "failed")
    )


def _tool_browser(tab: QWidget) -> QWidget:
    tools = tab.findChild(QWidget, widget_ids.MCP_CLIENT_TOOL_BROWSER)
    assert tools is not None
    return tools


def _tool_visible_blob(tools: QWidget) -> str:
    parts: list[str] = [_widget_text(tools)]
    count = _tool_item_count(tools)
    item_fn = getattr(tools, "item", None)
    if callable(item_fn):
        for index in range(count):
            item = item_fn(index)
            if item is None:
                continue
            parts.append(str(item.text()))
            parts.append(str(item.toolTip()))
            parts.append(str(item.data(Qt.ItemDataRole.UserRole) or ""))
    elif isinstance(tools, QListWidget):
        for index in range(tools.count()):
            item = tools.item(index)
            if item is None:
                continue
            parts.append(str(item.text()))
            parts.append(str(item.toolTip()))
    return " ".join(parts)


def _wait_connect_settled(tab: McpClientTab, mock_client: MagicMock) -> None:
    wait_until(
        lambda: (
            (
                _is_connected_badge(tab)
                and _tool_item_count(_tool_browser(tab)) >= 0
                and mock_client.run.called
            )
            or (
                _is_failed_or_disconnected_badge(tab)
                and bool(_error_text(tab))
            )
        ),
        timeout=_CONNECT_SETTLE_S,
        message="Connect did not settle (badge, tools, or error)",
        condition_name="mcp_client_connect_settled",
    )


def test_connect_lists_tools_in_browser(qapp) -> None:
    """FR-1 / FR-2: Connect calls list_tools and fills name + description."""
    mock_client = MagicMock()
    mock_client.run.return_value = _tools_response()
    tab = _build_draft_tab(mcp_client=mock_client)
    _set_url(tab, _MCP_URL)
    _click_connect(tab)
    _wait_connect_settled(tab, mock_client)

    mock_client.run.assert_called()
    _args, kwargs = mock_client.run.call_args
    assert "list_tools" in _args or kwargs.get("operation") == "list_tools"
    assert "headers" in kwargs
    assert isinstance(kwargs["headers"], dict)

    tools = _tool_browser(tab)
    assert _tool_item_count(tools) == 1
    blob = _tool_visible_blob(tools).lower()
    assert "echo" in blob
    assert "echo tool" in blob
    assert _is_connected_badge(tab)
    assert tab.objectName() == MCP_CLIENT_TAB_PAGE
    assert tab.findChild(QWidget, METHOD_COMBO) is None


def test_connect_empty_url_does_not_call_run_or_connect(qapp) -> None:
    """FR-1.4: empty URL is a failed Connect, not a local success."""
    mock_client = MagicMock()
    tab = _build_draft_tab(mcp_client=mock_client)
    _set_url(tab, "")
    _click_connect(tab)
    _wait_connect_settled(tab, mock_client)

    mock_client.run.assert_not_called()
    assert not _is_connected_badge(tab)
    assert _is_failed_or_disconnected_badge(tab)
    assert _tool_item_count(_tool_browser(tab)) == 0
    assert _error_text(tab)


def test_connect_error_leaves_disconnected_and_empty_tools(
    caplog,
    qapp,
) -> None:
    """FR-3: ExecutionError from run leaves not-connected chrome and no tools."""
    mock_client = MagicMock()
    mock_client.run.side_effect = ExecutionError(
        category=ErrorCategory.NETWORK,
        message="Could not connect to MCP server. Is it running?",
        detail="token=super-secret-token",
    )
    tab = _build_draft_tab(
        mcp_client=mock_client,
        env_vars={"token": "super-secret-token"},
        hidden_keys={"token"},
        url=_MCP_URL,
    )
    logger_name = "pypost.ui.presenters.mcp_client_presenter"
    with caplog.at_level(logging.ERROR, logger=logger_name):
        _click_connect(tab)
        _wait_connect_settled(tab, mock_client)

    assert not _is_connected_badge(tab)
    assert _is_failed_or_disconnected_badge(tab)
    assert _tool_item_count(_tool_browser(tab)) == 0
    error = _error_text(tab)
    assert error
    assert "super-secret-token" not in error
    assert tab.objectName() == MCP_CLIENT_TAB_PAGE
    error_messages = [
        record.getMessage()
        for record in caplog.records
        if record.name == logger_name
    ]
    assert any("mcp_client_list_tools_failed" in msg for msg in error_messages)
    joined = " ".join(error_messages)
    assert "super-secret-token" not in joined
    assert "headers" not in joined.lower()
    assert _MCP_URL not in joined


def test_refresh_failure_keeps_connected_and_stale_tools(qapp) -> None:
    """FR-4.3: failed Refresh stays connected and keeps the last-known list."""
    mock_client = MagicMock()
    mock_client.run.return_value = _tools_response(
        [
            {"name": "echo", "description": "Echo tool"},
            {"name": "ping", "description": "Ping tool"},
        ],
    )
    tab = _build_draft_tab(mcp_client=mock_client, url=_MCP_URL)
    refresh = _refresh_button(tab)
    assert refresh is not None, "MCP Client chrome must include a Refresh control"
    assert refresh.text().replace("&", "") == "Refresh"
    _click_connect(tab)
    _wait_connect_settled(tab, mock_client)
    wait_until(
        lambda: _tool_item_count(_tool_browser(tab)) == 2,
        timeout=_CONNECT_SETTLE_S,
        message="Connect did not populate the tool browser",
        condition_name="mcp_client_tools_populated",
    )
    prior_count = _tool_item_count(_tool_browser(tab))
    prior_blob = _tool_visible_blob(_tool_browser(tab))

    mock_client.run.side_effect = ExecutionError(
        category=ErrorCategory.TIMEOUT,
        message="Timed out listing MCP tools.",
    )
    refresh = _refresh_button(tab)
    assert refresh is not None
    refresh.click()
    wait_until(
        lambda: (
            bool(_error_text(tab))
            and "refreshing" not in _error_text(tab).lower()
            and _is_connected_badge(tab)
        ),
        timeout=_CONNECT_SETTLE_S,
        message="Refresh did not settle with an error",
        condition_name="mcp_client_refresh_settled",
    )

    assert _is_connected_badge(tab)
    assert not _is_failed_or_disconnected_badge(tab)
    tools = _tool_browser(tab)
    assert _tool_item_count(tools) == prior_count
    after_blob = _tool_visible_blob(tools)
    assert "echo" in after_blob.lower()
    assert "ping" in after_blob.lower()
    assert prior_blob == after_blob
    assert _error_text(tab)
    assert _tool_item_count(tools) != 0


def test_connect_forwards_resolved_url_and_headers(qapp) -> None:
    """FR-1.3: live Connect passes resolved URL and headers into run."""
    mock_client = MagicMock()
    mock_client.run.return_value = _tools_response()
    tab = _build_draft_tab(
        mcp_client=mock_client,
        env_vars={"host": "127.0.0.1:1080", "token": "secret"},
        url="http://{{host}}/mcp",
        headers={"Authorization": "Bearer {{token}}"},
    )
    _click_connect(tab)
    _wait_connect_settled(tab, mock_client)

    mock_client.run.assert_called_once_with(
        _MCP_URL,
        "list_tools",
        None,
        headers={"Authorization": "Bearer secret"},
    )


def test_connect_success_logs_tool_count_not_url_or_headers(caplog, qapp) -> None:
    """INFO list_tools success reports count only (NFR-4 / NFR-7)."""
    mock_client = MagicMock()
    mock_client.run.return_value = _tools_response()
    tab = _build_draft_tab(mcp_client=mock_client, url=_MCP_URL)
    logger_name = "pypost.ui.presenters.mcp_client_presenter"
    with caplog.at_level(logging.INFO, logger=logger_name):
        _click_connect(tab)
        _wait_connect_settled(tab, mock_client)
    messages = [
        record.getMessage()
        for record in caplog.records
        if record.name == logger_name
    ]
    connection_id = tab.connection_data.id
    assert any(
        "mcp_client_list_tools_succeeded" in msg
        and f"connection_id={connection_id}" in msg
        and "kind=connect" in msg
        and "tool_count=1" in msg
        for msg in messages
    )
    joined = " ".join(messages)
    assert "echo" not in joined.lower()
    assert "http://" not in joined
    assert "headers" not in joined.lower()


def test_connect_and_refresh_record_outbound_metrics(qapp) -> None:
    """NFR-7: Connect/Refresh increment outbound counters, not inbound MCP."""
    from pypost.core.metrics_registry import MetricsRegistry
    from prometheus_client import generate_latest

    registry = MetricsRegistry()
    mock_client = MagicMock()
    mock_client.run.return_value = _tools_response()
    tab = _build_draft_tab(
        mcp_client=mock_client,
        url=_MCP_URL,
        metrics=registry,
    )
    _click_connect(tab)
    _wait_connect_settled(tab, mock_client)
    scrape = generate_latest(registry.registry).decode("utf-8")
    assert 'mcp_client_connect_total{result="success"} 1.0' in scrape
    assert (
        'mcp_client_list_tools_total{operation="connect",result="success"} 1.0'
        in scrape
    )
    assert "mcp_requests_received_total" not in scrape or (
        "mcp_requests_received_total{" not in scrape
    )

    mock_client.run.side_effect = ExecutionError(
        category=ErrorCategory.TIMEOUT,
        message="Timed out listing MCP tools.",
    )
    refresh = _refresh_button(tab)
    assert refresh is not None
    refresh.click()
    wait_until(
        lambda: (
            bool(_error_text(tab))
            and "refreshing" not in _error_text(tab).lower()
            and _is_connected_badge(tab)
        ),
        timeout=_CONNECT_SETTLE_S,
        message="Refresh did not settle with an error",
        condition_name="mcp_client_refresh_metrics_settled",
    )
    scrape = generate_latest(registry.registry).decode("utf-8")
    assert 'mcp_client_connect_total{result="success"} 1.0' in scrape
    assert (
        'mcp_client_list_tools_total{operation="refresh",result="error"} 1.0'
        in scrape
    )
