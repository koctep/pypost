"""Automated failing repro tests for PYPOST-1453: adaptive join on dialog worker teardown.

Asserts contracts defined in ai-tasks/PYPOST-1453/20-architecture.md:
1. adaptive_thread_join supports polymorphic duck-typed QThread workers (isRunning / wait).
2. dialog.reject() performs fast adaptive teardown (<100ms) without rigid wait(1000).
3. dialog.closeEvent() and dialog.accept() use centralized teardown without rigid wait(1000).
4. Interactive collection switch cleans up prior fetch worker instead of abandoning it un-joined.
5. Unresponsive worker enforces bounded deadline and logs diagnostic warning.
6. None or already-stopped worker returns instantly without calling wait().
7. adaptive_thread_join emits structured debug polling slices, drain progress, and success logs.
8. _cancel_and_join_worker catches and logs exceptions raised by worker.cancel() (caplog C1).
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any
from unittest.mock import MagicMock

import pytest

from pypost.core.cancellation import AdaptiveJoinPolicy, adaptive_thread_join
from pypost.models.models import Environment
from pypost.ui.dialogs.import_collection_variables_dialog import (
    ImportCollectionVariablesDialog,
)

pytestmark = pytest.mark.timeout(30)


class DuckTypedWorkerDouble:
    """Simulates a PySide6 QThread background worker with isRunning() and wait(msecs)."""

    def __init__(self, run_duration_s: float = 0.010, name: str = "qthread-double") -> None:
        self.name = name
        self._running = True
        self._stop_event = threading.Event()
        self._run_duration = run_duration_s
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        self._stop_event.wait(self._run_duration)
        self._running = False

    def isRunning(self) -> bool:
        return self._running

    def wait(self, msecs: int = 0) -> bool:
        timeout = msecs / 1000.0 if msecs > 0 else None
        self._thread.join(timeout=timeout)
        return not self._running


class DynamicWorkerDouble:
    """Deterministic worker double tracking cancel and wait calls with simulated termination."""

    def __init__(
        self,
        name: str = "worker",
        exit_after_waits: int = 1,
        generation_id: int = 1,
    ) -> None:
        self.name = name
        self.generation_id = generation_id
        self._running = True
        self.cancel_count = 0
        self.wait_calls: list[int | float] = []
        self._exit_after_waits = exit_after_waits

    def cancel(self) -> None:
        self.cancel_count += 1

    def isRunning(self) -> bool:
        return self._running

    def wait(self, msecs: int = 0) -> bool:
        self.wait_calls.append(msecs)
        if len(self.wait_calls) >= self._exit_after_waits:
            self._running = False
        return not self._running


class UnresponsiveWorkerDouble:
    """Worker double that ignores cancellation and remains running past deadlines."""

    def __init__(self, name: str = "UnresponsiveWorker", generation_id: int = 1) -> None:
        self.name = name
        self.generation_id = generation_id
        self.cancel_count = 0
        self.wait_calls: list[int | float] = []

    def cancel(self) -> None:
        self.cancel_count += 1

    def isRunning(self) -> bool:
        return True

    def wait(self, msecs: int = 0) -> bool:
        self.wait_calls.append(msecs)
        if msecs > 0:
            time.sleep(min(msecs / 1000.0, 0.015))
        return False


class AlreadyStoppedWorkerDouble:
    """Worker double that is already stopped (isRunning() == False)."""

    def __init__(self, name: str = "StoppedWorker", generation_id: int = 1) -> None:
        self.name = name
        self.generation_id = generation_id
        self.cancel_count = 0
        self.wait_calls: list[int | float] = []

    def cancel(self) -> None:
        self.cancel_count += 1

    def isRunning(self) -> bool:
        return False

    def wait(self, msecs: int = 0) -> bool:
        self.wait_calls.append(msecs)
        return True


class FailingCancelWorkerDouble:
    """Worker double whose cancel() method raises an unexpected exception."""

    def __init__(self, name: str = "FaultyWorker", generation_id: int = 1) -> None:
        self.name = name
        self.generation_id = generation_id
        self._running = True

    def cancel(self) -> None:
        raise RuntimeError("simulated cancellation dispatch failure")

    def isRunning(self) -> bool:
        return self._running

    def wait(self, msecs: int = 0) -> bool:
        self._running = False
        return True


def _create_dialog(qapp: Any) -> ImportCollectionVariablesDialog:
    """Create a minimal headless ImportCollectionVariablesDialog."""
    env = Environment(name="DevEnv", variables={})
    dialog = ImportCollectionVariablesDialog(
        target_environment=env,
        workspace_collections=[],
        library_service=None,
    )
    return dialog


@pytest.mark.timeout(10)
def test_adaptive_thread_join_polymorphic_qthread_support() -> None:
    """adaptive_thread_join must support duck-typed QThread workers (isRunning and wait)."""
    worker = DuckTypedWorkerDouble(run_duration_s=0.010, name="qthread-worker")

    start_time = time.monotonic()
    joined = adaptive_thread_join(worker, timeout=1.0)
    elapsed = time.monotonic() - start_time

    assert joined is True
    assert not worker.isRunning()
    assert elapsed < 0.150, f"Adaptive join took too long: {elapsed:.3f}s"


@pytest.mark.timeout(10)
def test_dialog_reject_adaptive_teardown_fast_latency(qapp: Any) -> None:
    """dialog.reject() must cancel and adaptively join workers without rigid wait(1000)."""
    dialog = _create_dialog(qapp)

    mock_discovery = DynamicWorkerDouble(name="DiscoveryWorker", exit_after_waits=1)
    mock_fetch = DynamicWorkerDouble(name="FetchWorker", exit_after_waits=1)
    dialog._active_discovery_worker = mock_discovery  # type: ignore[assignment]
    dialog._active_fetch_worker = mock_fetch  # type: ignore[assignment]

    start_time = time.monotonic()
    dialog.reject()
    elapsed = time.monotonic() - start_time

    assert elapsed < 0.200, f"Reject took too long: {elapsed:.3f}s"
    assert dialog._active_discovery_worker is None
    assert dialog._active_fetch_worker is None
    assert mock_discovery.cancel_count == 1
    assert mock_fetch.cancel_count == 1
    assert 1000 not in mock_discovery.wait_calls, (
        f"Rigid 1000ms wait executed on discovery worker: {mock_discovery.wait_calls}"
    )
    assert 1000 not in mock_fetch.wait_calls, (
        f"Rigid 1000ms wait executed on fetch worker: {mock_fetch.wait_calls}"
    )
    assert hasattr(dialog, "_cancel_fetch_worker"), (
        "Dialog must define centralized _cancel_fetch_worker helper"
    )


@pytest.mark.timeout(10)
def test_dialog_close_event_and_accept_centralized_teardown(qapp: Any) -> None:
    """closeEvent and accept must use centralized teardown helpers without wait(1000)."""
    dialog = _create_dialog(qapp)

    assert hasattr(dialog, "_cancel_fetch_worker"), (
        "Dialog must define centralized _cancel_fetch_worker helper"
    )
    assert hasattr(dialog, "_cancel_and_join_worker"), (
        "Dialog must define centralized _cancel_and_join_worker helper"
    )

    mock_discovery = DynamicWorkerDouble(name="DiscoveryWorker", exit_after_waits=1)
    mock_fetch = DynamicWorkerDouble(name="FetchWorker", exit_after_waits=1)
    dialog._active_discovery_worker = mock_discovery  # type: ignore[assignment]
    dialog._active_fetch_worker = mock_fetch  # type: ignore[assignment]

    close_event = MagicMock()
    dialog.closeEvent(close_event)
    assert dialog._active_discovery_worker is None
    assert dialog._active_fetch_worker is None
    assert mock_discovery.cancel_count == 1
    assert mock_fetch.cancel_count == 1
    assert 1000 not in mock_discovery.wait_calls
    assert 1000 not in mock_fetch.wait_calls

    mock_discovery2 = DynamicWorkerDouble(name="DiscoveryWorker2", exit_after_waits=1)
    mock_fetch2 = DynamicWorkerDouble(name="FetchWorker2", exit_after_waits=1)
    dialog._active_discovery_worker = mock_discovery2  # type: ignore[assignment]
    dialog._active_fetch_worker = mock_fetch2  # type: ignore[assignment]

    dialog.accept()
    assert dialog._active_discovery_worker is None
    assert dialog._active_fetch_worker is None
    assert mock_discovery2.cancel_count == 1
    assert mock_fetch2.cancel_count == 1
    assert 1000 not in mock_discovery2.wait_calls
    assert 1000 not in mock_fetch2.wait_calls


@pytest.mark.timeout(10)
def test_interactive_collection_switch_cleans_up_previous_fetch_worker(qapp: Any) -> None:
    """Collection selection switch must cancel and wait previous fetch worker."""
    dialog = _create_dialog(qapp)

    mock_fetch = DynamicWorkerDouble(name="PreviousFetchWorker", exit_after_waits=1)
    dialog._active_fetch_worker = mock_fetch  # type: ignore[assignment]

    dialog.collection_combo.setCurrentIndex(-1)
    dialog._on_collection_changed()

    assert mock_fetch.cancel_count == 1
    assert len(mock_fetch.wait_calls) > 0, (
        "Previous fetch worker must be joined/waited on collection switch, not abandoned"
    )
    assert 1000 not in mock_fetch.wait_calls


@pytest.mark.timeout(10)
def test_unresponsive_worker_enforces_bounded_deadline_and_logs_warning(
    qapp: Any,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Unresponsive worker must respect custom timeout and emit deadline warning log."""
    dialog = _create_dialog(qapp)

    assert hasattr(dialog, "_cancel_fetch_worker"), (
        "Dialog must define centralized _cancel_fetch_worker helper"
    )
    worker = UnresponsiveWorkerDouble(name="StubbornFetchWorker")
    dialog._active_fetch_worker = worker  # type: ignore[assignment]

    with caplog.at_level(logging.WARNING):
        start_time = time.monotonic()
        dialog._cancel_fetch_worker(timeout=0.080)
        elapsed = time.monotonic() - start_time

    assert elapsed < 0.250, f"Teardown exceeded bounded deadline: {elapsed:.3f}s"
    assert dialog._active_fetch_worker is None
    assert worker.cancel_count == 1
    warning_records = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert any(
        "exceeded join deadline" in r.message and "StubbornFetchWorker" in r.message
        for r in warning_records
    ), f"Expected deadline warning not found in logs: {[r.message for r in warning_records]}"


@pytest.mark.timeout(10)
def test_none_or_already_stopped_worker_returns_instantly(qapp: Any) -> None:
    """Teardown on None or already-stopped worker must return instantly without calling wait."""
    dialog = _create_dialog(qapp)

    dialog._active_discovery_worker = None
    stopped_worker = AlreadyStoppedWorkerDouble(name="StoppedWorker")
    dialog._active_fetch_worker = stopped_worker  # type: ignore[assignment]

    start_time = time.monotonic()
    dialog.reject()
    elapsed = time.monotonic() - start_time

    assert elapsed < 0.050, f"Teardown took too long for stopped worker: {elapsed:.3f}s"
    assert dialog._active_fetch_worker is None
    assert len(stopped_worker.wait_calls) == 0, (
        f"Wait was called on already stopped worker: {stopped_worker.wait_calls}"
    )


class SlowDrainWorkerDouble:
    """Worker double that simulates a brief draining delay with actual wait sleep."""

    def __init__(self, exit_after_waits: int = 2, name: str = "DrainWorker") -> None:
        self.name = name
        self._running = True
        self.wait_calls: list[int | float] = []
        self._exit_after_waits = exit_after_waits

    def isRunning(self) -> bool:
        return self._running

    def wait(self, msecs: int = 0) -> bool:
        self.wait_calls.append(msecs)
        time.sleep(0.010)
        if len(self.wait_calls) >= self._exit_after_waits:
            self._running = False
        return not self._running


@pytest.mark.timeout(10)
def test_adaptive_thread_join_structured_debug_and_progress_logs(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """adaptive_thread_join logs debug polling slices, drain progress, and success."""
    worker = SlowDrainWorkerDouble(name="ProgressWorker", exit_after_waits=2)
    policy = AdaptiveJoinPolicy(
        initial_poll=0.008,
        multiplier=1.2,
        max_poll=0.050,
        progress_log_interval=0.005,
    )

    with caplog.at_level(logging.DEBUG, logger="pypost.core.cancellation"):
        joined = adaptive_thread_join(worker, timeout=1.0, policy=policy)

    assert joined is True
    assert not worker.isRunning()

    messages = [r.message for r in caplog.records if r.name == "pypost.core.cancellation"]

    slice_logs = [m for m in messages if "Adaptive thread join polling slice:" in m]
    assert len(slice_logs) >= 2, f"Expected polling slice logs, got: {slice_logs}"
    assert "thread=ProgressWorker" in slice_logs[0]

    drain_logs = [m for m in messages if "Waiting for worker thread to drain:" in m]
    assert len(drain_logs) >= 1, f"Expected drain progress log, got: {messages}"
    assert "thread=ProgressWorker" in drain_logs[0]

    success_logs = [m for m in messages if "Adaptive thread join succeeded:" in m]
    assert len(success_logs) == 1, f"Expected 1 success log, got: {success_logs}"
    assert "thread=ProgressWorker" in success_logs[0]


@pytest.mark.timeout(10)
def test_dialog_cancel_worker_logs_error_on_cancel_exception(
    qapp: Any,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """_cancel_and_join_worker catches and logs exception if worker.cancel() fails (caplog C1)."""
    dialog = _create_dialog(qapp)
    worker = FailingCancelWorkerDouble(name="FaultyWorker")

    with caplog.at_level(
        logging.ERROR,
        logger="pypost.ui.dialogs.import_collection_variables_dialog",
    ):
        joined = dialog._cancel_and_join_worker(worker, name="FaultyWorker", timeout=0.5)

    assert joined is True
    error_records = [
        r
        for r in caplog.records
        if r.name == "pypost.ui.dialogs.import_collection_variables_dialog"
        and r.levelno == logging.ERROR
    ]
    assert len(error_records) == 1
    assert "Error requesting cancellation on FaultyWorker" in error_records[0].message
    assert error_records[0].exc_info is not None
