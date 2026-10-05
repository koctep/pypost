"""PYPOST-1289: session-end metrics across outputs and workspace lifecycle routes."""

import pytest
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from prometheus_client import generate_latest

from pypost.core.metrics_otel import OtelMetricsTracker
from pypost.core.metrics_protocol import MetricsTrackerProtocol, NullMetrics
from pypost.core.metrics_registry import MetricsRegistry
from pypost.core.qt.metrics import MetricsManager
from pypost.models.mcp_client import McpClientSessionState
from pypost.models.response import ResponseData
from pypost.models.settings import AppSettings
from pypost.ui.presenters.tabs_presenter import TabsPresenter
from pypost.ui.widgets.new_tab_protocol_picker import TabProtocol
from tests.test_tabs_presenter import FakeRequestManager, FakeStateManager

pytestmark = pytest.mark.timeout(30)


@pytest.mark.parametrize("factory", [MetricsRegistry, MetricsManager])
def test_prometheus_disconnect_outputs(qapp, factory) -> None:
    tracker = factory()
    assert isinstance(tracker, MetricsTrackerProtocol)
    for reason in ("user", "error", "teardown", "user"):
        tracker.track_mcp_client_disconnect(reason)
    output = generate_latest(tracker.registry).decode()
    samples = [line for line in output.splitlines() if line.startswith(
        "mcp_client_disconnect_total{"
    )]
    assert set(samples) == {
        'mcp_client_disconnect_total{reason="user"} 2.0',
        'mcp_client_disconnect_total{reason="error"} 1.0',
        'mcp_client_disconnect_total{reason="teardown"} 1.0',
    }


def test_otel_disconnect_outputs() -> None:
    reader = InMemoryMetricReader()
    provider = MeterProvider(metric_readers=[reader])
    try:
        tracker = OtelMetricsTracker(meter=provider.get_meter("disconnect-test"))
        for reason in ("user", "error", "teardown", "user"):
            tracker.track_mcp_client_disconnect(reason)
        data = reader.get_metrics_data()
        points = [
            point
            for resource in data.resource_metrics
            for scope in resource.scope_metrics
            for metric in scope.metrics
            if metric.name == "mcp_client_disconnect_total"
            for point in metric.data.data_points
        ]
        assert {tuple(point.attributes) for point in points} == {("reason",)}
        assert {point.attributes["reason"]: point.value for point in points} == {
            "user": 2, "error": 1, "teardown": 1,
        }
    finally:
        provider.shutdown()


def test_disabled_disconnect_metrics() -> None:
    tracker = NullMetrics()
    assert isinstance(tracker, MetricsTrackerProtocol)
    for reason in ("user", "error", "teardown"):
        assert tracker.track_mcp_client_disconnect(reason) is None


@pytest.mark.parametrize("route", ["button", "f5", "tab", "profile", "application"])
def test_workspace_session_end_routes(qapp, route) -> None:
    metrics = MetricsRegistry()
    workspace = TabsPresenter(
        FakeRequestManager(), FakeStateManager(), AppSettings(), metrics=metrics,
        protocol_picker=lambda *_args, **_kwargs: TabProtocol.HTTP,
    )
    tab = workspace.add_blank_mcp_client_tab(save_state=False)
    workspace._tabs.setCurrentWidget(tab)
    client = tab.presenter
    client._on_list_ok(
        client._outbound_generation, "connect",
        ResponseData(
            status_code=200, headers={}, body='{"tools": []}', elapsed_time=0.01, size=13,
        ),
    )
    assert client.state == McpClientSessionState.CONNECTED
    try:
        if route == "button":
            tab.disconnect_btn.click()
        elif route == "f5":
            workspace.handle_f5_global()
        elif route == "tab":
            workspace.close_tab(workspace._tabs.indexOf(tab))
        elif route == "profile":
            workspace.close_tabs_for_mcp_client_ids(
                [tab.connection_data.id], prompt=lambda *_args, **_kwargs: True,
            )
        else:
            workspace.teardown()
        assert client.state == McpClientSessionState.DISCONNECTED
        workspace.teardown()
        client.teardown()
        reason = "user" if route in ("button", "f5") else "teardown"
        samples = [
            sample for metric in metrics.registry.collect()
            for sample in metric.samples if sample.name == "mcp_client_disconnect_total"
        ]
        assert [(sample.labels, sample.value) for sample in samples] == [({"reason": reason}, 1)]
    finally:
        workspace.teardown()
        workspace._tabs.deleteLater()


def test_declining_profile_close_keeps_session(qapp) -> None:
    metrics = MetricsRegistry()
    workspace = TabsPresenter(
        FakeRequestManager(), FakeStateManager(), AppSettings(), metrics=metrics,
        protocol_picker=lambda *_args, **_kwargs: TabProtocol.HTTP,
    )
    tab = workspace.add_blank_mcp_client_tab(save_state=False)
    tab.presenter._on_list_ok(
        tab.presenter._outbound_generation, "connect",
        ResponseData(
            status_code=200, headers={}, body='{"tools": []}', elapsed_time=0.01, size=13,
        ),
    )
    try:
        workspace.close_tabs_for_mcp_client_ids(
            [tab.connection_data.id], prompt=lambda *_args, **_kwargs: False,
        )
        assert workspace._tabs.indexOf(tab) >= 0
        assert tab.presenter.state == McpClientSessionState.CONNECTED
        assert metrics.registry.get_sample_value(
            "mcp_client_disconnect_total", {"reason": "teardown"},
        ) is None
    finally:
        workspace.teardown()
        workspace._tabs.deleteLater()
