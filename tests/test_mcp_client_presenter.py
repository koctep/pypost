"""PYPOST-1167: MCP Client presenter resolves URL/headers and forwards them."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock

import pytest

from pypost.core.metrics_protocol import MetricsTrackerProtocol
from pypost.models.mcp_client import McpClientConnection
from pypost.models.response import ResponseData
from pypost.ui.presenters.mcp_client_presenter import McpClientPresenter

pytestmark = pytest.mark.timeout(10)

_ENV = {"host": "127.0.0.1:1080", "token": "secret"}
_RESOLVED_URL = "http://127.0.0.1:1080/mcp"
_RESOLVED_HEADERS = {"Authorization": "Bearer secret"}


def _ok_response() -> ResponseData:
    return ResponseData(
        status_code=200,
        headers={},
        body="{}",
        elapsed_time=0.01,
        size=2,
    )


def test_execute_outbound_forwards_resolved_url_and_headers() -> None:
    """FR-2 / FR-3: execute_outbound sends rendered URL and headers to run()."""
    mock_client = MagicMock()
    mock_client.run.return_value = _ok_response()
    presenter = McpClientPresenter(
        McpClientConnection(
            url="http://{{host}}/mcp",
            headers={"Authorization": "Bearer {{token}}"},
        ),
        env_vars=_ENV,
        mcp_client=mock_client,
    )

    presenter.execute_outbound("list_tools")

    mock_client.run.assert_called_once_with(
        _RESOLVED_URL,
        "list_tools",
        None,
        headers=_RESOLVED_HEADERS,
    )


def test_execute_outbound_forwards_empty_headers() -> None:
    """Empty connection headers still call run with headers={}."""
    mock_client = MagicMock()
    mock_client.run.return_value = _ok_response()
    presenter = McpClientPresenter(
        McpClientConnection(url="http://{{host}}/mcp", headers={}),
        env_vars=_ENV,
        mcp_client=mock_client,
    )

    presenter.execute_outbound("list_tools")

    mock_client.run.assert_called_once_with(
        _RESOLVED_URL,
        "list_tools",
        None,
        headers={},
    )


def test_resolve_outbound_fields_logs_header_count_not_values(caplog) -> None:
    """DEBUG resolve log is count-only; secret header values stay out of logs."""
    presenter = McpClientPresenter(
        McpClientConnection(
            url="http://{{host}}/mcp",
            headers={"Authorization": "Bearer {{token}}"},
        ),
        env_vars=_ENV,
    )
    logger_name = "pypost.ui.presenters.mcp_client_presenter"
    with caplog.at_level(logging.DEBUG, logger=logger_name):
        presenter.resolve_outbound_fields()
    messages = [
        record.getMessage()
        for record in caplog.records
        if record.name == logger_name
    ]
    joined = " ".join(messages)
    assert any(
        "mcp_client_outbound_fields_resolved" in msg
        and f"connection_id={presenter.connection.id}" in msg
        and "header_count=1" in msg
        for msg in messages
    )
    assert "secret" not in joined
    assert "Bearer" not in joined
    assert "Authorization" not in joined
    assert "{{token}}" not in joined
    assert "{{host}}" not in joined


def test_empty_url_connect_records_error_metrics_without_run() -> None:
    """Empty URL Connect increments outbound error counters and never calls run."""
    mock_client = MagicMock()
    metrics = MagicMock(spec=MetricsTrackerProtocol)
    presenter = McpClientPresenter(
        McpClientConnection(url=""),
        mcp_client=mock_client,
        metrics=metrics,
    )
    presenter.connect_requested()
    mock_client.run.assert_not_called()
    metrics.track_mcp_client_connect.assert_called_once_with("error")
    metrics.track_mcp_client_list_tools.assert_called_once_with("error", "connect")


def test_refresh_initiated_log_omits_url_and_headers(caplog) -> None:
    """Refresh INFO is connection_id only (no URL, secrets, or headers)."""
    presenter = McpClientPresenter(
        McpClientConnection(url="http://127.0.0.1:1080/mcp"),
    )
    logger_name = "pypost.ui.presenters.mcp_client_presenter"
    with caplog.at_level(logging.INFO, logger=logger_name):
        presenter.refresh_requested()
    messages = [
        record.getMessage()
        for record in caplog.records
        if record.name == logger_name
    ]
    assert any(
        "mcp_client_refresh_initiated" in msg
        and f"connection_id={presenter.connection.id}" in msg
        for msg in messages
    )
    joined = " ".join(messages)
    assert "http://" not in joined
    assert "headers" not in joined.lower()
