"""Shared values for bounded asynchronous owner teardown."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import threading
from typing import Any
from uuid import uuid4


_LIFECYCLE_OWNER_BY_CLASS = {
    "MainWindow": "main_window",
    "TabsPresenter": "tabs_presenter",
    "EnvPresenter": "env_presenter",
    "HistoryPanel": "history_panel",
    "HistoryManager": "history_manager",
    "EnvironmentStorageGateway": "environment_storage_gateway",
}


@dataclass(frozen=True)
class TeardownResult:
    """Observable result of one owner teardown attempt."""

    owner: str
    outcome: str
    elapsed_ms: int
    active_count: int = 0
    pending_count: int = 0
    failure_kind: str | None = None
    dispositions: dict[int, str] | None = None


@dataclass(frozen=True)
class EnvironmentUpdateRecord:
    """Durable request-to-storage handoff record."""

    sequence: int
    variables: dict[str, str]
    disposition: str


class EnvironmentUpdateLedger:
    """Thread-safe acceptance ledger for request-produced environment updates."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._next_sequence = 0
        self._records: dict[int, EnvironmentUpdateRecord] = {}
        self._dispositions: dict[int, str] = {}

    def accept(self, variables: dict[str, str], admitted: bool) -> int:
        with self._lock:
            self._next_sequence += 1
            sequence = self._next_sequence
            self._records[sequence] = EnvironmentUpdateRecord(
                sequence=sequence,
                variables=deepcopy(variables),
                disposition="pending" if admitted else "rejected_after_cutoff",
            )
            self._dispositions[sequence] = self._records[sequence].disposition
            return sequence

    def cutoff(self) -> int:
        with self._lock:
            return self._next_sequence

    def pending(self, cutoff: int | None = None) -> list[EnvironmentUpdateRecord]:
        with self._lock:
            limit = self._next_sequence if cutoff is None else cutoff
            return [
                record
                for record in self._records.values()
                if record.sequence <= limit and record.disposition == "pending"
            ]

    def mark(self, sequence: int, disposition: str) -> None:
        with self._lock:
            record = self._records.get(sequence)
            if record is None or record.disposition != "pending":
                return
            self._records[sequence] = EnvironmentUpdateRecord(
                sequence=record.sequence,
                variables=record.variables,
                disposition=disposition,
            )
            self._dispositions[sequence] = disposition

    def dispositions_view(self) -> dict[int, str]:
        """Return the live scalar disposition view used by teardown results."""
        return self._dispositions


def teardown_correlation_id(owner: Any) -> str:
    """Return one safe correlation id for an owner teardown attempt."""
    correlation_id = getattr(owner, "_teardown_correlation_id", None)
    if correlation_id is None:
        correlation_id = uuid4().hex
        setattr(owner, "_teardown_correlation_id", correlation_id)
    return correlation_id


def record_teardown_metrics(owner: Any, result: TeardownResult, metrics: Any = None) -> None:
    """Record one terminal teardown sample without requiring telemetry injection."""
    tracker = getattr(metrics, "track_lifecycle_teardown", None)
    if callable(tracker):
        tracker(
            result.owner,
            result.outcome,
            result.elapsed_ms / 1000.0,
            result.active_count,
            result.pending_count,
        )


def record_lifecycle_event(
    owner: Any, event: str, count: int = 1, metrics: Any = None
) -> None:
    """Record a bounded-cardinality lifecycle event, if metrics are available."""
    tracker = getattr(metrics, "track_lifecycle_event", None)
    if callable(tracker):
        metric_owner = getattr(owner, "_lifecycle_metric_owner", None)
        if metric_owner is None:
            metric_owner = _LIFECYCLE_OWNER_BY_CLASS.get(type(owner).__name__, "unknown")
        tracker(metric_owner, event, count)


def record_environment_update_disposition(
    disposition: str, metrics: Any = None
) -> None:
    tracker = getattr(metrics, "track_environment_update_disposition", None)
    if callable(tracker):
        tracker(disposition)


def record_history_io_failure(operation: str, metrics: Any = None) -> None:
    tracker = getattr(metrics, "track_history_io_failure", None)
    if callable(tracker):
        tracker(operation)
