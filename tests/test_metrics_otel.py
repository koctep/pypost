"""Tests for OtelMetricsTracker (PYPOST-579)."""

import pytest
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader

from pypost.core.metrics_otel import OtelMetricsTracker, create_otel_metrics_tracker
from pypost.core.metrics_protocol import MetricsTrackerProtocol
from pypost.models.errors import ErrorCategory

pytestmark = pytest.mark.timeout(30)


@pytest.fixture(scope="module")
def otel_reader():
    """Single MeterProvider for the module — OTel allows one global provider."""
    reader = InMemoryMetricReader()
    provider = MeterProvider(metric_readers=[reader])
    metrics.set_meter_provider(provider)
    return reader, provider


def _counter_value(reader, name: str, attributes: dict | None = None) -> int | None:
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
                    attrs = dict(point.attributes)
                    if attributes is None or attrs == attributes:
                        return int(point.value)
    return None


def _histogram_count(reader, name: str, attributes: dict) -> int | None:
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
                        return int(point.count)
    return None


def test_otel_tracker_satisfies_protocol(otel_reader):
    _reader, provider = otel_reader
    tracker = OtelMetricsTracker(meter=provider.get_meter("protocol-test"))
    assert isinstance(tracker, MetricsTrackerProtocol)


def test_create_otel_metrics_tracker_factory(otel_reader):
    reader, _provider = otel_reader
    tracker = create_otel_metrics_tracker(meter_name="factory-test")
    assert isinstance(tracker, MetricsTrackerProtocol)
    tracker.track_gui_send_click()
    assert _counter_value(reader, "gui_send_clicks_total") == 1


def test_track_request_sent_increments_counter(otel_reader):
    reader, provider = otel_reader
    tracker = OtelMetricsTracker(meter=provider.get_meter("request-sent-test"))
    tracker.track_request_sent("GET")
    tracker.track_request_sent("GET")
    assert _counter_value(reader, "requests_sent_total", {"method": "GET"}) == 2


def test_track_mcp_param_default_applied_increments_counter(otel_reader):
    reader, provider = otel_reader
    tracker = OtelMetricsTracker(meter=provider.get_meter("param-default-test"))
    tracker.track_mcp_param_default_applied("GET")
    tracker.track_mcp_param_default_applied("GET")
    assert (
        _counter_value(reader, "mcp_param_defaults_applied_total", {"method": "GET"})
        == 2
    )


def test_track_mcp_client_connect_and_list_tools_increments_counters(otel_reader):
    reader, provider = otel_reader
    tracker = OtelMetricsTracker(meter=provider.get_meter("mcp-client-outbound-test"))
    tracker.track_mcp_client_connect("success")
    tracker.track_mcp_client_list_tools("error", "refresh")
    assert _counter_value(
        reader, "mcp_client_connect_total", {"result": "success"}
    ) == 1
    assert _counter_value(
        reader,
        "mcp_client_list_tools_total",
        {"result": "error", "operation": "refresh"},
    ) == 1


def test_track_mcp_client_call_tool_increments_counter(otel_reader):
    reader, provider = otel_reader
    tracker = OtelMetricsTracker(
        meter=provider.get_meter("mcp-client-call-tool-test"),
    )
    tracker.track_mcp_client_call_tool("success")
    tracker.track_mcp_client_call_tool("error")
    assert _counter_value(
        reader, "mcp_client_call_tool_total", {"result": "success"}
    ) == 1
    assert _counter_value(
        reader, "mcp_client_call_tool_total", {"result": "error"}
    ) == 1


def test_track_mcp_tool_call_duration_records_histogram(otel_reader):
    reader, provider = otel_reader
    tracker = OtelMetricsTracker(meter=provider.get_meter("histogram-test"))
    tracker.track_mcp_tool_call_duration("tools/call", "success", 0.25)
    assert (
        _histogram_count(
            reader,
            "mcp_tool_call_duration_seconds",
            {"method": "tools/call", "status": "success"},
        )
        == 1
    )


def test_track_mcp_library_metrics_records_bounded_labels_and_durations(otel_reader):
    reader, provider = otel_reader
    tracker = OtelMetricsTracker(meter=provider.get_meter("mcp-library-metrics-test"))
    tracker.track_mcp_library_discovery("unexpected", "unexpected", -1.0, -3)
    tracker.track_mcp_library_validation("unexpected")
    tracker.track_mcp_library_save("unexpected", -1.0)

    assert _counter_value(
        reader,
        "mcp_library_discovery_total",
        {"operation": "unknown", "outcome": "unknown"},
    ) == 1
    assert _histogram_count(
        reader,
        "mcp_library_discovery_duration_seconds",
        {"operation": "unknown", "outcome": "unknown"},
    ) == 1
    assert _histogram_count(
        reader, "mcp_library_discovery_items", {"operation": "unknown"}
    ) == 1
    assert _counter_value(
        reader, "mcp_library_validation_total", {"category": "unknown"}
    ) == 1
    assert _counter_value(
        reader, "mcp_library_save_outcomes_total", {"outcome": "unknown"}
    ) == 1
    assert _histogram_count(
        reader, "mcp_library_save_duration_seconds", {"outcome": "unknown"}
    ) == 1


def test_track_template_expression_render_duration_records_histogram(otel_reader):
    reader, provider = otel_reader
    tracker = OtelMetricsTracker(meter=provider.get_meter("template-duration-test"))
    tracker.track_template_expression_render_duration("hover", 0.001)
    assert (
        _histogram_count(
            reader,
            "template_expression_render_duration_seconds",
            {"render_path": "hover"},
        )
        == 1
    )


def test_set_mcp_server_up_updates_internal_state(otel_reader):
    _reader, provider = otel_reader
    tracker = OtelMetricsTracker(meter=provider.get_meter("gauge-test"))
    tracker.set_mcp_server_up(True)
    assert tracker._mcp_server_ready == 1
    observations = list(tracker._observe_mcp_server_up(None))
    assert observations[0].value == 1
    tracker.set_mcp_server_up(False)
    assert tracker._mcp_server_ready == 0
    observations = list(tracker._observe_mcp_server_up(None))
    assert observations[0].value == 0


def test_mcp_server_instance_counts_are_exported_without_instance_labels(otel_reader):
    _reader, provider = otel_reader
    tracker = OtelMetricsTracker(meter=provider.get_meter("instance-counts-test"))
    tracker.set_mcp_server_instance_counts({"running": 2, "failed": 1})
    observations = list(tracker._observe_mcp_server_instance_counts(None))
    assert {(item.attributes["state"], item.value) for item in observations} == {
        ("stopped", 0),
        ("starting", 0),
        ("running", 2),
        ("failed", 1),
    }
    assert tracker._mcp_server_ready == 1


def test_track_request_error_uses_category_value(otel_reader):
    reader, provider = otel_reader
    tracker = OtelMetricsTracker(meter=provider.get_meter("error-test"))
    tracker.track_request_error(ErrorCategory.NETWORK)
    assert (
        _counter_value(reader, "request_errors_total", {"category": "network"}) == 1
    )


def test_track_gui_new_tab_action_normalizes_unknown_source(otel_reader):
    reader, provider = otel_reader
    tracker = OtelMetricsTracker(meter=provider.get_meter("new-tab-test"))
    tracker.track_gui_new_tab_action("custom_source")
    assert (
        _counter_value(
            reader,
            "gui_new_tab_actions_total",
            {"source": "unknown", "protocol": "unknown"},
        )
        == 1
    )


def test_track_gui_new_tab_action_records_mcp_client_protocol(otel_reader):
    reader, provider = otel_reader
    tracker = OtelMetricsTracker(
        meter=provider.get_meter("new-tab-mcp-client-test"),
    )
    unknown_before = _counter_value(
        reader,
        "gui_new_tab_actions_total",
        {"source": "shortcut", "protocol": "unknown"},
    )
    tracker.track_gui_new_tab_action("shortcut", protocol="mcp_client")
    assert (
        _counter_value(
            reader,
            "gui_new_tab_actions_total",
            {"source": "shortcut", "protocol": "mcp_client"},
        )
        == 1
    )
    unknown_after = _counter_value(
        reader,
        "gui_new_tab_actions_total",
        {"source": "shortcut", "protocol": "unknown"},
    )
    assert unknown_after == unknown_before
