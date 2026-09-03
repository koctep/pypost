"""Tests for PYPOST-1100 MCP validation observability."""

from __future__ import annotations

import asyncio
import logging
from unittest.mock import MagicMock, patch

import pytest
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader

from pypost.core.mcp_activity_log import McpActivityLog
from pypost.core.mcp_server_impl import MCPServerImpl
from pypost.core.metrics_otel import OtelMetricsTracker
from pypost.core.metrics_protocol import MetricsTrackerProtocol
from pypost.core.metrics_registry import MetricsRegistry
from pypost.models.models import McpToolParam, RequestData
from pypost.models.websocket import WebSocketConnection

pytestmark = pytest.mark.timeout(60)


def _otel_counter_value(
    reader: InMemoryMetricReader,
    name: str,
    attributes: dict[str, str],
) -> int | None:
    reader.collect()
    data = reader.get_metrics_data()
    if data is None:
        return None
    for resource_metrics in data.resource_metrics:
        for scope_metrics in resource_metrics.scope_metrics:
            for metric in scope_metrics.metrics:
                if metric.name != name:
                    continue
                for point in metric.data.data_points:
                    if dict(point.attributes) == attributes:
                        return int(point.value)
    return None


def test_registry_validation_counter_uses_bounded_labels() -> None:
    registry = MetricsRegistry()
    registry.track_mcp_argument_validation_failure(
        "preflight", "websocket", "integer"
    )
    registry.track_mcp_argument_validation_failure(
        "untrusted-stage", "untrusted-transport", "untrusted-type"
    )

    output = next(
        metric
        for metric in registry.registry.collect()
        if metric.name == "mcp_argument_validation_failures"
    )
    samples = {
        tuple(
            sample.labels[label] for label in ("stage", "transport", "declared_type")
        ): sample.value
        for sample in output.samples
        if sample.name.endswith("_total")
    }
    assert samples[("preflight", "websocket", "integer")] == 1.0
    assert samples[("unknown", "unknown", "unknown")] == 1.0
    assert all("untrusted" not in str(labels) for labels in samples)


def test_otel_validation_counter_uses_same_labels() -> None:
    reader = InMemoryMetricReader()
    provider = MeterProvider(metric_readers=[reader])
    meter = provider.get_meter("mcp-validation-observability-test")
    tracker = OtelMetricsTracker(meter=meter)
    tracker.track_mcp_argument_validation_failure(
        "execution_boundary", "http", "integer_or_string"
    )

    assert _otel_counter_value(
        reader,
        "mcp_argument_validation_failures_total",
        {
            "stage": "execution_boundary",
            "transport": "http",
            "declared_type": "integer_or_string",
        },
    ) == 1


def test_http_preflight_failure_records_safe_observability(
    caplog: pytest.LogCaptureFixture,
) -> None:
    metrics = MagicMock(spec=MetricsTrackerProtocol)
    activity_log = McpActivityLog()
    impl = MCPServerImpl(metrics=metrics, activity_log=activity_log)
    request = RequestData(
        name="Typed Tool",
        expose_as_mcp=True,
        method="POST",
        url="http://example.com",
        mcp_params={"count": McpToolParam(type="integer", required=True)},
    )
    impl.register_tools([request])
    raw_value = "sensitive-count"

    with caplog.at_level(logging.WARNING, logger="pypost.core.mcp_observability"):
        with pytest.raises(Exception):
            asyncio.run(impl.call_tool("typed_tool", {"count": raw_value}))

    messages = [record.getMessage() for record in caplog.records]
    assert len(messages) == 1
    assert "mcp_argument_validation_failed" in messages[0]
    assert "stage=preflight" in messages[0]
    assert "transport=http" in messages[0]
    assert "tool=typed_tool" in messages[0]
    assert "param=count" in messages[0]
    assert "expected_type=integer" in messages[0]
    assert raw_value not in messages[0]
    metrics.track_mcp_argument_validation_failure.assert_called_once_with(
        "preflight", "http", "integer"
    )
    metrics.track_mcp_response_sent.assert_called_once_with("POST", "validation_error")
    duration_call = metrics.track_mcp_tool_call_duration.call_args.args
    assert duration_call[:2] == ("POST", "validation_error")
    assert duration_call[2] >= 0.0

    entries = activity_log.get_entries()
    assert len(entries) == 1
    assert entries[0].outcome == "validation_error"
    assert entries[0].tool_name == "typed_tool"
    assert entries[0].mcp_arg_count == 1
    assert entries[0].http_status is None
    assert entries[0].duration_ms is not None
    assert entries[0].detail is not None
    assert "count" in entries[0].detail
    assert "integer" in entries[0].detail
    assert raw_value not in entries[0].detail


def test_websocket_preflight_failure_records_validation_outcome_without_probe(
    caplog: pytest.LogCaptureFixture,
) -> None:
    metrics = MagicMock(spec=MetricsTrackerProtocol)
    activity_log = McpActivityLog()
    impl = MCPServerImpl(metrics=metrics, activity_log=activity_log)
    connection = WebSocketConnection(
        name="Typed Feed",
        expose_as_mcp=True,
        url="ws://example.com",
        mcp_params={"count": McpToolParam(type="integer", required=True)},
    )
    impl.register_tools([connection])
    probe = MagicMock(return_value=[])

    with patch("pypost.core.mcp_server_impl.execute_websocket_probe", probe):
        with caplog.at_level(logging.WARNING, logger="pypost.core.mcp_observability"):
            with pytest.raises(Exception):
                asyncio.run(impl.call_tool("ws_typed_feed", {"count": "bad"}))

    probe.assert_not_called()
    metrics.track_mcp_argument_validation_failure.assert_called_once_with(
        "preflight", "websocket", "integer"
    )
    metrics.track_mcp_response_sent.assert_called_once_with(
        "WEBSOCKET", "validation_error"
    )
    duration_call = metrics.track_mcp_tool_call_duration.call_args.args
    assert duration_call[:2] == ("WEBSOCKET", "validation_error")
    assert len(activity_log.get_entries()) == 1
    assert activity_log.get_entries()[0].outcome == "validation_error"
    assert activity_log.get_entries()[0].http_status is None


def test_http_execution_boundary_failure_records_distinct_stage(
    caplog: pytest.LogCaptureFixture,
) -> None:
    metrics = MagicMock(spec=MetricsTrackerProtocol)
    activity_log = McpActivityLog()
    impl = MCPServerImpl(metrics=metrics, activity_log=activity_log)
    request = RequestData(
        name="Legacy Default Tool",
        expose_as_mcp=True,
        method="GET",
        url="http://example.com",
        mcp_params={
            "identifier": McpToolParam(
                type="integer_or_string", required=False, default="legacy-id"
            )
        },
    )
    impl.register_tools([request])
    service = MagicMock()
    impl._create_request_service = lambda: service

    with caplog.at_level(logging.WARNING, logger="pypost.core.mcp_observability"):
        with pytest.raises(Exception):
            asyncio.run(impl.call_tool("legacy_default_tool", {}))

    messages = [record.getMessage() for record in caplog.records]
    assert len(messages) == 1
    assert "stage=execution_boundary" in messages[0]
    assert "transport=http" in messages[0]
    assert "param=identifier" in messages[0]
    assert "expected_type=integer_or_string" in messages[0]
    assert "legacy-id" not in messages[0]
    metrics.track_mcp_request_received.assert_called_once_with("GET")
    metrics.track_mcp_argument_validation_failure.assert_called_once_with(
        "execution_boundary", "http", "integer_or_string"
    )
    metrics.track_mcp_response_sent.assert_called_once_with("GET", "validation_error")
    service.execute.assert_not_called()
    entries = activity_log.get_entries()
    assert len(entries) == 1
    assert entries[0].outcome == "validation_error"
    assert entries[0].duration_ms is not None
    assert entries[0].http_status is None


def test_default_application_log_excludes_secret_and_large_default(
    caplog: pytest.LogCaptureFixture,
) -> None:
    metrics = MagicMock(spec=MetricsTrackerProtocol)
    impl = MCPServerImpl(metrics=metrics)
    secret = "sensitive-default-token"
    large_default = [secret] * 128
    request = RequestData(
        name="Secret Default Tool",
        expose_as_mcp=True,
        method="GET",
        url="http://example.com",
        mcp_params={
            "tokens": McpToolParam(type="array", required=False, default=large_default),
        },
    )
    impl.register_tools([request])
    service = MagicMock()
    service.execute.return_value = {"status": 200, "body": "ok"}
    impl._create_request_service = lambda: service

    with caplog.at_level(logging.INFO, logger="pypost.core.mcp_server_impl"):
        asyncio.run(impl.call_tool("secret_default_tool", {}))

    messages = [
        record.getMessage()
        for record in caplog.records
        if "mcp_param_default_applied" in record.getMessage()
    ]
    assert len(messages) == 1
    assert "method=GET" in messages[0]
    assert "param=tokens" in messages[0]
    assert "default_applied=true" in messages[0]
    assert "default_type=array" in messages[0]
    assert secret not in messages[0]
    assert repr(large_default) not in messages[0]
