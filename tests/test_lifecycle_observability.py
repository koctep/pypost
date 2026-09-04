"""PYPOST-1256: lifecycle logs and metrics remain useful at shutdown."""

from __future__ import annotations

import logging
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from prometheus_client import generate_latest

from pypost.core.history_manager import HistoryManager
from pypost.core.lifecycle import EnvironmentUpdateLedger, TeardownResult
from pypost.core.metrics_otel import OtelMetricsTracker
from pypost.core.metrics_registry import MetricsRegistry
from pypost.models.settings import AppSettings
from pypost.ui.main_window_lifecycle import teardown as teardown_main_window
from pypost.ui.presenters.env_presenter import EnvPresenter
from pypost.ui.presenters.tabs_presenter import TabsPresenter
from tests.test_tabs_presenter import FakeRequestManager, FakeStateManager, _make_request

pytestmark = pytest.mark.timeout(60)


def _messages(caplog: pytest.LogCaptureFixture, event: str) -> list[str]:
    return [
        record.getMessage()
        for record in caplog.records
        if event in record.getMessage()
    ]


def _teardown_ids(messages: list[str]) -> set[str]:
    return {
        message.split("teardown_id=", 1)[1].split()[0]
        for message in messages
        if "teardown_id=" in message
    }


def _scrape(metrics: MetricsRegistry) -> str:
    return generate_latest(metrics.registry).decode("utf-8")


def _otel_points(reader: InMemoryMetricReader, name: str) -> list[object]:
    reader.collect()
    data = reader.get_metrics_data()
    assert data is not None
    points = []
    for resource_metrics in data.resource_metrics:
        for scope_metrics in resource_metrics.scope_metrics:
            for metric in scope_metrics.metrics:
                if metric.name == name:
                    points.extend(metric.data.data_points)
    return points


def _make_tabs_presenter(metrics: MetricsRegistry) -> TabsPresenter:
    request_manager = FakeRequestManager()
    state_manager = FakeStateManager()
    return TabsPresenter(
        request_manager,
        state_manager,
        AppSettings(),
        metrics=metrics,
        protocol_picker=lambda *_args, **_kwargs: None,
    )


def _make_env_presenter(metrics: MetricsRegistry) -> EnvPresenter:
    storage = MagicMock()
    storage.load_environments.return_value = []
    storage.serialize_environment_records.side_effect = lambda environments, **_kwargs: [
        environment.model_dump(mode="json") for environment in environments
    ]
    return EnvPresenter(
        storage,
        MagicMock(),
        MagicMock(),
        AppSettings(env_encryption_enabled=True),
        lambda: [],
        metrics,
    )


def test_history_teardown_emits_correlated_terminal_log_and_metrics(tmp_path, caplog):
    metrics = MetricsRegistry()
    manager = HistoryManager(history_path=tmp_path / "history.json", metrics=metrics)

    with caplog.at_level(logging.INFO, logger="pypost.core.history_manager"):
        result = manager.teardown(timeout_ms=100)

    assert result.outcome == "success"
    started = _messages(caplog, "lifecycle_teardown_started")
    completed = _messages(caplog, "lifecycle_teardown_completed")
    assert len(started) == len(completed) == 1
    assert _teardown_ids(started) == _teardown_ids(completed)
    assert "owner=history_manager" in completed[0]
    assert "deadline_ms=100" in completed[0]
    scraped = _scrape(metrics)
    assert (
        'lifecycle_teardowns_total{outcome="success",owner="history_manager"} 1.0'
        in scraped
    )
    assert 'lifecycle_teardown_active_workers{owner="history_manager"} 0.0' in scraped


def test_history_load_failure_is_counted_without_recording_payload(tmp_path, caplog):
    path = tmp_path / "history.json"
    path.write_text("not-json", encoding="utf-8")
    metrics = MetricsRegistry()

    with caplog.at_level(logging.WARNING, logger="pypost.core.history_manager"):
        HistoryManager(history_path=path, metrics=metrics)

    assert 'history_io_failures_total{operation="load"} 1.0' in _scrape(metrics)
    assert all("not-json" not in record.getMessage() for record in caplog.records)


def test_request_teardown_logs_correlated_start_and_completion_once(qapp, caplog):
    metrics = MetricsRegistry()
    presenter = _make_tabs_presenter(metrics)
    presenter.add_new_tab(_make_request("request"), save_state=False)

    logger_name = "pypost.ui.presenters.tabs_presenter_lifecycle"
    with caplog.at_level(logging.INFO, logger=logger_name):
        result = presenter.teardown(timeout_ms=100)
        repeated = presenter.teardown(timeout_ms=100)

    assert result == repeated
    started = _messages(caplog, "lifecycle_teardown_started")
    completed = _messages(caplog, "lifecycle_teardown_completed")
    assert len(started) == len(completed) == 1
    assert _teardown_ids(started) == _teardown_ids(completed)
    assert "owner=tabs_presenter" in started[0]
    assert "owner=tabs_presenter" in completed[0]
    assert (
        'lifecycle_teardowns_total{outcome="success",owner="tabs_presenter"} 1.0'
        in _scrape(metrics)
    )


def test_environment_teardown_suppresses_late_signal_and_keeps_safe_context(
    qapp, caplog
):
    metrics = MetricsRegistry()
    presenter = _make_env_presenter(metrics)
    with caplog.at_level(
        logging.INFO,
        logger="pypost.ui.presenters.env_presenter_lifecycle",
    ):
        result = presenter.teardown(timeout_ms=100)
        presenter._on_storage_load_completed([])
        presenter._on_storage_load_failed("super-secret-storage-error")
        with patch("pypost.ui.presenters.env_presenter.show_env_save_failed") as show_error:
            presenter._on_storage_save_failed("super-secret-save-error")

    assert result.outcome == "success"
    assert show_error.call_count == 0
    late_messages = _messages(caplog, "lifecycle_late_delivery_ignored")
    assert len(late_messages) == 3
    assert all("super-secret" not in message for message in late_messages)
    assert (
        'lifecycle_events_total{event="late_signal_suppressed",owner="env_presenter"} 3.0'
        in _scrape(metrics)
    )


class _AggregateOwner:
    def __init__(self, owner: str) -> None:
        self.owner = owner
        self.begin_calls = 0

    def begin_teardown(self) -> None:
        self.begin_calls += 1

    def teardown(self, timeout_ms: int | None = None) -> TeardownResult:
        return TeardownResult(self.owner, "success", 1)


def test_main_window_aggregate_logs_and_metrics_one_correlated_attempt(caplog):
    metrics = MetricsRegistry()
    owners = {
        name: _AggregateOwner(name)
        for name in ("tabs", "history_panel", "history_manager", "env")
    }
    window = SimpleNamespace(
        tabs=owners["tabs"],
        history_panel=owners["history_panel"],
        history_manager=owners["history_manager"],
        env=owners["env"],
        metrics=metrics,
        _teardown_lock=None,
        _teardown_result=None,
        _teardown_started=False,
    )

    with caplog.at_level(logging.INFO, logger="pypost.ui.main_window_lifecycle"):
        result = teardown_main_window(window, timeout_ms=100)

    assert result.outcome == "success"
    started = _messages(caplog, "lifecycle_teardown_started")
    completed = _messages(caplog, "lifecycle_teardown_completed")
    assert len(started) == len(completed) == 1
    assert _teardown_ids(started) == _teardown_ids(completed)
    assert owners["tabs"].begin_calls == 1
    assert owners["history_panel"].begin_calls == 1
    assert owners["history_manager"].begin_calls == 1
    assert owners["env"].begin_calls == 1
    assert (
        'lifecycle_teardowns_total{outcome="success",owner="main_window"} 1.0'
        in _scrape(metrics)
    )


def test_environment_ledger_records_every_terminal_disposition():
    metrics = MetricsRegistry()
    ledger = EnvironmentUpdateLedger()
    sequences = [
        ledger.accept({"safe": str(index)}, admitted=True) for index in range(4)
    ]
    rejected = ledger.accept({"safe": "rejected"}, admitted=False)
    dispositions = (
        "persisted",
        "coalesced_into_newer_save",
        "failed",
        "incomplete",
    )
    for sequence, disposition in zip(sequences, dispositions):
        ledger.mark(sequence, disposition)
        metrics.track_environment_update_disposition(disposition)
    metrics.track_environment_update_disposition("rejected_after_cutoff")

    assert ledger.dispositions_view() == {
        sequences[0]: "persisted",
        sequences[1]: "coalesced_into_newer_save",
        sequences[2]: "failed",
        sequences[3]: "incomplete",
        rejected: "rejected_after_cutoff",
    }
    scraped = _scrape(metrics)
    for disposition in (*dispositions, "rejected_after_cutoff"):
        assert (
            f'environment_update_dispositions_total{{disposition="{disposition}"}} 1.0'
            in scraped
        )


def test_otel_lifecycle_metrics_normalize_labels_and_keep_payloads_out():
    reader = InMemoryMetricReader()
    provider = MeterProvider(metric_readers=[reader])
    tracker = OtelMetricsTracker(meter=provider.get_meter("lifecycle-observability"))

    tracker.track_lifecycle_teardown(
        "https://secret.example.test/token",
        "unexpected-outcome",
        0.25,
        active_count=-2,
        pending_count=3,
    )
    tracker.track_lifecycle_event("secret-owner", "secret-event")
    tracker.track_environment_update_disposition("persisted")
    tracker.track_history_io_failure("save")

    teardown_points = _otel_points(reader, "lifecycle_teardowns_total")
    assert len(teardown_points) == 1
    assert dict(teardown_points[0].attributes) == {
        "owner": "unknown",
        "outcome": "unknown",
    }
    active_points = _otel_points(reader, "lifecycle_teardown_active_workers")
    assert len(active_points) == 1
    assert active_points[0].value == 0
    assert dict(active_points[0].attributes) == {"owner": "unknown"}
    event_points = _otel_points(reader, "lifecycle_events_total")
    assert len(event_points) == 1
    assert dict(event_points[0].attributes) == {
        "owner": "unknown",
        "event": "unknown",
    }
    disposition_points = _otel_points(
        reader, "environment_update_dispositions_total"
    )
    assert len(disposition_points) == 1
    assert dict(disposition_points[0].attributes) == {"disposition": "persisted"}
    history_points = _otel_points(reader, "history_io_failures_total")
    assert len(history_points) == 1
    assert dict(history_points[0].attributes) == {"operation": "save"}
    all_attributes = repr(
        [
            dict(point.attributes)
            for metric_name in (
                "lifecycle_teardowns_total",
                "lifecycle_events_total",
                "environment_update_dispositions_total",
                "history_io_failures_total",
            )
            for point in _otel_points(reader, metric_name)
        ]
    )
    assert "secret" not in all_attributes
