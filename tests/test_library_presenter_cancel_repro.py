"""Failing repro tests for LibraryPresenter cooperative cancel & dialog teardown (PYPOST-1497).

These tests reproduce missing presenter cancellation and dialog close lifecycle methods:
1. test_presenter_cancel_single_operation_cooperative_abort:
   Demonstrates missing operation_cancelled signals, missing cancel_operation() method,
   and unreleased admission lock on worker cancellation.
2. test_presenter_cancel_nonexistent_operation_returns_false:
   Demonstrates missing cancel_operation() method on non-existent operation key.
3. test_presenter_cancel_all_operations_bulk_teardown:
   Demonstrates missing cancel_all_operations() method and bulk worker termination.
4. test_presenter_teardown_idempotent:
   Demonstrates missing teardown() and close() methods, state marking, and idempotency.
5. test_presenter_teardown_suppresses_late_results_and_errors:
   Demonstrates missing late result/failure suppression when presenter is torn down.
6. test_presenter_teardown_idle_instant_return:
   Demonstrates missing teardown() instant exit when no operations are active.
7. test_dialog_close_triggers_presenter_teardown:
   Demonstrates missing closeEvent and reject overrides in LibraryManagerDialog calling
   presenter teardown.
"""
from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from pypost.core.git_service import GitLibraryService
from pypost.ui.dialogs.library_dialogs import LibraryManagerDialog
from pypost.ui.presenters.library_presenter import LibraryPresenter

pytestmark = [pytest.mark.timeout(30)]


@pytest.mark.timeout(30)
def test_presenter_cancel_single_operation_cooperative_abort(
    qapp: Any, tmp_path: Path
) -> None:
    """Missing cancel_operation() and operation_cancelled signals strand admission."""
    service = MagicMock(spec=GitLibraryService)
    service.base_dir = tmp_path
    presenter = LibraryPresenter(service=service)

    op_entered = threading.Event()
    op_cancelled = threading.Event()
    release = threading.Event()

    def cancellable_op(*, cancellation_token: Any | None = None) -> str:
        op_entered.set()
        while not release.is_set():
            if cancellation_token is not None and cancellation_token.is_cancellation_requested:
                op_cancelled.set()
                cancellation_token.throw_if_cancellation_requested()
            release.wait(timeout=0.02)
        return "done"

    cancelled_signals: list[str] = []
    cancelled_lib_signals: list[tuple[str, str]] = []

    # Desired signals on presenter:
    presenter.operation_cancelled.connect(cancelled_signals.append)
    presenter.operation_cancelled_for_library.connect(
        lambda lib, op: cancelled_lib_signals.append((lib, op))
    )

    try:
        started = presenter.run_operation_async("lib-1", "pull", cancellable_op)
        assert started is True
        assert op_entered.wait(timeout=5.0)
        assert ("lib-1", "pull") in presenter._active_operations

        # Desired cooperative cancellation method
        res = presenter.cancel_operation("lib-1", "pull")
        assert res is True

        assert op_cancelled.wait(timeout=5.0)

        # Bounded wait for worker thread to exit and process Qt events
        worker = presenter._workers.get(("lib-1", "pull"))
        if worker is not None:
            worker.wait(2000)
        qapp.processEvents()

        # Signals emitted
        assert "pull" in cancelled_signals
        assert ("lib-1", "pull") in cancelled_lib_signals

        # Admission lock released
        assert ("lib-1", "pull") not in presenter._active_operations

        # Verify admission is available for subsequent operation
        restarted = presenter.run_operation_async("lib-1", "pull", lambda: "ok")
        assert restarted is True
    finally:
        release.set()
        for worker in list(getattr(presenter, "_workers", {}).values()):
            worker.wait(1000)


@pytest.mark.timeout(30)
def test_presenter_cancel_nonexistent_operation_returns_false(
    qapp: Any, tmp_path: Path
) -> None:
    """cancel_operation() on an inactive operation returns False without error."""
    service = MagicMock(spec=GitLibraryService)
    service.base_dir = tmp_path
    presenter = LibraryPresenter(service=service)

    res = presenter.cancel_operation("lib-1", "nonexistent")
    assert res is False


@pytest.mark.timeout(30)
def test_presenter_cancel_all_operations_bulk_teardown(
    qapp: Any, tmp_path: Path
) -> None:
    """cancel_all_operations() cooperatively aborts all in-flight workers within timeout."""
    service = MagicMock(spec=GitLibraryService)
    service.base_dir = tmp_path
    presenter = LibraryPresenter(service=service)

    op1_entered = threading.Event()
    op2_entered = threading.Event()
    op1_cancelled = threading.Event()
    op2_cancelled = threading.Event()
    release = threading.Event()

    def cancellable_op1(*, cancellation_token: Any | None = None) -> str:
        op1_entered.set()
        while not release.is_set():
            if cancellation_token is not None and cancellation_token.is_cancellation_requested:
                op1_cancelled.set()
                cancellation_token.throw_if_cancellation_requested()
            release.wait(timeout=0.02)
        return "done1"

    def cancellable_op2(*, cancellation_token: Any | None = None) -> str:
        op2_entered.set()
        while not release.is_set():
            if cancellation_token is not None and cancellation_token.is_cancellation_requested:
                op2_cancelled.set()
                cancellation_token.throw_if_cancellation_requested()
            release.wait(timeout=0.02)
        return "done2"

    try:
        assert presenter.run_operation_async("lib-1", "pull", cancellable_op1) is True
        assert presenter.run_operation_async("lib-2", "refresh", cancellable_op2) is True
        assert op1_entered.wait(timeout=5.0)
        assert op2_entered.wait(timeout=5.0)
        assert len(presenter._active_operations) == 2

        res = presenter.cancel_all_operations(timeout_ms=1000)
        assert res is True
        assert op1_cancelled.wait(timeout=5.0)
        assert op2_cancelled.wait(timeout=5.0)

        qapp.processEvents()

        workers = list(getattr(presenter, "_workers", {}).values())
        for w in workers:
            assert not w.isRunning()
    finally:
        release.set()
        for worker in list(getattr(presenter, "_workers", {}).values()):
            worker.wait(1000)


@pytest.mark.timeout(30)
def test_presenter_teardown_idempotent(
    qapp: Any, tmp_path: Path
) -> None:
    """teardown() and close() are idempotent, cancel active operations, and mark torn down."""
    service = MagicMock(spec=GitLibraryService)
    service.base_dir = tmp_path
    presenter = LibraryPresenter(service=service)

    op_entered = threading.Event()
    release = threading.Event()

    def cancellable_op(*, cancellation_token: Any | None = None) -> str:
        op_entered.set()
        while not release.is_set():
            if cancellation_token is not None and cancellation_token.is_cancellation_requested:
                cancellation_token.throw_if_cancellation_requested()
            release.wait(timeout=0.02)
        return "done"

    try:
        presenter.run_operation_async("lib-1", "pull", cancellable_op)
        assert op_entered.wait(timeout=5.0)

        # First teardown call
        presenter.teardown(timeout_ms=500)
        assert getattr(presenter, "_torn_down", False) is True
        assert len(presenter._active_operations) == 0

        # Second teardown call (idempotent)
        presenter.teardown(timeout_ms=500)
        assert getattr(presenter, "_torn_down", False) is True

        # Close convenience alias
        presenter.close(timeout_ms=500)
        assert getattr(presenter, "_torn_down", False) is True
    finally:
        release.set()
        for worker in list(getattr(presenter, "_workers", {}).values()):
            worker.wait(1000)


@pytest.mark.timeout(30)
def test_presenter_teardown_suppresses_late_results_and_errors(
    qapp: Any, tmp_path: Path
) -> None:
    """Torn down presenter suppresses late completion and failure signal emissions."""
    service = MagicMock(spec=GitLibraryService)
    service.base_dir = tmp_path
    presenter = LibraryPresenter(service=service)

    completed_signals: list[object] = []
    failed_signals: list[object] = []
    presenter.operation_completed.connect(completed_signals.append)
    presenter.operation_failed.connect(failed_signals.append)

    # Presenter is torn down
    presenter.teardown(timeout_ms=500)
    assert getattr(presenter, "_torn_down", False) is True

    # Simulate late worker results/errors attempting delivery after teardown
    presenter._worker_succeeded(("lib-1", "pull"), MagicMock())
    presenter._worker_failed(("lib-1", "pull"), RuntimeError("late error"))

    # Assertions: signals must be suppressed
    assert len(completed_signals) == 0, "Late completion must be suppressed after teardown"
    assert len(failed_signals) == 0, "Late failure must be suppressed after teardown"


@pytest.mark.timeout(30)
def test_presenter_teardown_idle_instant_return(
    qapp: Any, tmp_path: Path
) -> None:
    """Idle presenter teardown returns immediately without burning timeout budget."""
    service = MagicMock(spec=GitLibraryService)
    service.base_dir = tmp_path
    presenter = LibraryPresenter(service=service)

    assert len(presenter._active_operations) == 0
    start = time.monotonic()
    presenter.teardown(timeout_ms=2000)
    elapsed = time.monotonic() - start

    assert elapsed < 0.1, f"Idle teardown took {elapsed:.3f}s, expected < 0.1s"
    assert getattr(presenter, "_torn_down", False) is True


@pytest.mark.timeout(30)
def test_dialog_close_triggers_presenter_teardown(
    qapp: Any, tmp_path: Path
) -> None:
    """LibraryManagerDialog close and reject trigger presenter.teardown()."""
    service = MagicMock(spec=GitLibraryService)
    service.base_dir = tmp_path
    presenter = LibraryPresenter(service=service)

    teardown_spy = MagicMock()
    presenter.teardown = teardown_spy

    dialog = LibraryManagerDialog(presenter=presenter)
    try:
        dialog.show()
        qapp.processEvents()

        # Closing the dialog must trigger presenter.teardown()
        dialog.close()
        qapp.processEvents()
        teardown_spy.assert_called_once()

        # Rejecting the dialog must also trigger presenter.teardown()
        teardown_spy.reset_mock()
        dialog.reject()
        qapp.processEvents()
        teardown_spy.assert_called_once()
    finally:
        dialog.deleteLater()
        qapp.processEvents()


@pytest.mark.timeout(30)
def test_presenter_cancel_operation_logging_and_metrics_contract(
    qapp: Any, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Cancellation emits library_presenter_operation_cancelled and suppresses failure logs."""
    service = MagicMock(spec=GitLibraryService)
    service.base_dir = tmp_path
    metrics = MagicMock()
    presenter = LibraryPresenter(service=service, metrics=metrics)

    op_entered = threading.Event()
    op_cancelled = threading.Event()
    release = threading.Event()

    def cancellable_op(*, cancellation_token: Any | None = None) -> str:
        op_entered.set()
        while not release.is_set():
            if cancellation_token is not None and cancellation_token.is_cancellation_requested:
                op_cancelled.set()
                cancellation_token.throw_if_cancellation_requested()
            release.wait(timeout=0.02)
        return "done"

    logger_name = "pypost.ui.presenters.library_presenter"
    with caplog.at_level(logging.INFO, logger=logger_name):
        assert presenter.run_operation_async("lib-obs", "pull", cancellable_op) is True
        assert op_entered.wait(timeout=5.0)

        assert presenter.cancel_operation("lib-obs", "pull") is True
        assert op_cancelled.wait(timeout=5.0)

        worker = presenter._workers.get(("lib-obs", "pull"))
        if worker is not None:
            worker.wait(2000)
        qapp.processEvents()

    release.set()

    # Rule C1/C5: verify structured log events
    cancelling_records = [
        r for r in caplog.records
        if "library_presenter_operation_cancelling" in r.message
    ]
    assert len(cancelling_records) == 1
    assert "library_id=lib-obs" in cancelling_records[0].message
    assert "operation=pull" in cancelling_records[0].message

    cancelled_records = [
        r for r in caplog.records
        if "library_presenter_operation_cancelled" in r.message
    ]
    assert len(cancelled_records) == 1
    assert "library_id=lib-obs" in cancelled_records[0].message
    assert "operation=pull" in cancelled_records[0].message

    # Verify failure logs are suppressed: no ERROR logs emitted
    error_records = [r for r in caplog.records if r.levelno >= logging.ERROR]
    assert len(error_records) == 0, f"Expected no error logs on cancel, got: {error_records}"

    # Verify metrics tracking
    metrics.track_gui_library_operation.assert_any_call("pull", "cancelled")


@pytest.mark.timeout(30)
def test_presenter_teardown_logging_and_suppression_contract(
    qapp: Any, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Teardown emits started/completed logs and suppresses late failure logs."""
    service = MagicMock(spec=GitLibraryService)
    service.base_dir = tmp_path
    presenter = LibraryPresenter(service=service)

    op_entered = threading.Event()
    release = threading.Event()

    def cancellable_op(*, cancellation_token: Any | None = None) -> str:
        op_entered.set()
        while not release.is_set():
            if cancellation_token is not None and cancellation_token.is_cancellation_requested:
                cancellation_token.throw_if_cancellation_requested()
            release.wait(timeout=0.02)
        return "done"

    logger_name = "pypost.ui.presenters.library_presenter"
    with caplog.at_level(logging.INFO, logger=logger_name):
        assert presenter.run_operation_async("lib-teardown", "refresh", cancellable_op) is True
        assert op_entered.wait(timeout=5.0)

        presenter.teardown(timeout_ms=1000)
        qapp.processEvents()

        # Simulate late worker failure after teardown
        presenter._worker_failed(("lib-teardown", "refresh"), RuntimeError("late error"))
        qapp.processEvents()

    release.set()

    # Rule C1/C5: verify teardown started and completed structured log events
    teardown_started_records = [
        r for r in caplog.records
        if "library_presenter_teardown_started" in r.message
    ]
    assert len(teardown_started_records) == 1
    assert "timeout_ms=1000" in teardown_started_records[0].message
    assert "active_ops=1" in teardown_started_records[0].message

    teardown_completed_records = [
        r for r in caplog.records
        if "library_presenter_teardown_completed" in r.message
    ]
    assert len(teardown_completed_records) == 1

    # Verify failure logs are suppressed: late _worker_failed suppresses failure log
    error_records = [r for r in caplog.records if r.levelno >= logging.ERROR]
    assert len(error_records) == 0, f"Expected no error logs after teardown, got: {error_records}"
