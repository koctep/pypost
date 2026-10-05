"""PYPOST-1167: MCP Client presenter resolves URL/headers and forwards them."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock

import pytest

from pypost.core.metrics_protocol import MetricsTrackerProtocol, NullMetrics
from pypost.models.mcp_client import McpClientConnection, McpClientSessionState
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


class _DisconnectRecorder(NullMetrics):
    """Record session ends while retaining no-op metrics for other operations."""

    def __init__(self) -> None:
        self.reasons: list[str] = []

    def track_mcp_client_disconnect(self, reason: str) -> None:
        self.reasons.append(reason)


@pytest.fixture
def disconnect_presenter() -> tuple[McpClientPresenter, _DisconnectRecorder]:
    metrics = _DisconnectRecorder()
    presenter = McpClientPresenter(
        McpClientConnection(url="http://example.invalid/mcp"),
        metrics=metrics,
    )
    return presenter, metrics


def _settle_connect(presenter: McpClientPresenter) -> None:
    """Deliver a valid Connect result without starting a worker or transport."""
    presenter._on_list_ok(
        presenter._outbound_generation,
        "connect",
        ResponseData(
            status_code=200,
            headers={},
            body='{"tools": []}',
            elapsed_time=0.01,
            size=13,
        ),
    )
    assert presenter.state == McpClientSessionState.CONNECTED


def test_disconnect_counts_once_per_established_session(disconnect_presenter) -> None:
    presenter, metrics = disconnect_presenter
    _settle_connect(presenter)

    presenter.disconnect_requested()
    assert presenter.state == McpClientSessionState.DISCONNECTED
    assert metrics.reasons == ["user"]
    presenter.disconnect_requested()
    presenter.teardown()
    assert metrics.reasons == ["user"]

    _settle_connect(presenter)
    presenter.disconnect_requested()
    assert metrics.reasons == ["user", "user"]


def test_teardown_counts_once_for_established_session(disconnect_presenter) -> None:
    presenter, metrics = disconnect_presenter
    _settle_connect(presenter)

    presenter.teardown()
    assert presenter.state == McpClientSessionState.DISCONNECTED
    assert metrics.reasons == ["teardown"]
    presenter.teardown()
    presenter.disconnect_requested()
    assert metrics.reasons == ["teardown"]


def test_terminal_error_release_counts_once_for_established_session(disconnect_presenter) -> None:
    presenter, metrics = disconnect_presenter
    _settle_connect(presenter)

    # Ordinary operation failures are nonterminal; exercise the release boundary.
    presenter._release_session(reason="error")
    assert presenter.state == McpClientSessionState.DISCONNECTED
    assert metrics.reasons == ["error"]
    presenter._release_session(reason="error")
    presenter.teardown()
    assert metrics.reasons == ["error"]


def test_failed_connect_does_not_count_disconnect(disconnect_presenter, caplog) -> None:
    presenter, metrics = disconnect_presenter
    with caplog.at_level(logging.ERROR, logger="pypost.ui.presenters.mcp_client_presenter"):
        presenter._on_list_error(presenter._outbound_generation, "connect", "connect failed")
    assert "mcp_client_list_tools_failed" in caplog.text
    assert presenter.state == McpClientSessionState.FAILED
    presenter.disconnect_requested()
    presenter.teardown()
    assert metrics.reasons == []


def test_cancelled_connect_does_not_count_disconnect(disconnect_presenter) -> None:
    presenter, metrics = disconnect_presenter
    presenter._state = McpClientSessionState.CONNECTING
    presenter._list_in_flight = True

    presenter.disconnect_requested()
    presenter.teardown()
    assert presenter.state == McpClientSessionState.DISCONNECTED
    assert metrics.reasons == []


def test_tracker_failure_does_not_interrupt_release(disconnect_presenter, caplog) -> None:
    presenter, metrics = disconnect_presenter
    _settle_connect(presenter)
    presenter._tab = MagicMock()
    worker = MagicMock()
    presenter._worker = worker
    metrics.track_mcp_client_disconnect = MagicMock(side_effect=RuntimeError("secret"))
    with caplog.at_level(logging.WARNING, logger="pypost.ui.presenters.mcp_client_presenter"):
        presenter.disconnect_requested()
        presenter.teardown()
    assert presenter.state == McpClientSessionState.DISCONNECTED
    assert presenter._session is None
    assert presenter._worker is None
    presenter._tab.clear_tools.assert_called()
    presenter._tab.clear_invoke.assert_called()
    metrics.track_mcp_client_disconnect.assert_called_once_with("user")
    assert "mcp_client_disconnect_metric_failed reason=user" in caplog.text
    assert "secret" not in caplog.text


def test_stale_connect_result_cannot_reestablish_released_session(disconnect_presenter) -> None:
    presenter, metrics = disconnect_presenter
    _settle_connect(presenter)
    generation = presenter._outbound_generation
    presenter.disconnect_requested()
    presenter._on_list_ok(generation, "connect", _ok_response())
    presenter.teardown()
    assert presenter.state == McpClientSessionState.DISCONNECTED
    assert metrics.reasons == ["user"]


@pytest.mark.parametrize("kind", ["refresh", "invoke"])
def test_nonterminal_error_does_not_count_disconnect(disconnect_presenter, caplog, kind) -> None:
    presenter, metrics = disconnect_presenter
    _settle_connect(presenter)
    callback = presenter._on_list_error if kind == "refresh" else presenter._on_invoke_error
    with caplog.at_level(logging.ERROR, logger="pypost.ui.presenters.mcp_client_presenter"):
        callback(presenter._outbound_generation, kind, "operation failed")
    event = "mcp_client_list_tools_failed" if kind == "refresh" else "mcp_client_call_tool_failed"
    assert event in caplog.text
    assert presenter.state == McpClientSessionState.CONNECTED
    assert metrics.reasons == []
