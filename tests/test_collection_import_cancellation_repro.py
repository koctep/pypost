"""Reproduction tests for cooperative worker cancellation (PYPOST-1229, PYPOST-1265).

These tests cover cooperative cancellation in ``CollectionImportParseWorker``
and the ``CollectionImportActions.teardown()`` lifecycle. The PYPOST-1229 tests
were originally red reproductions and now verify the corrected behavior.

Scenarios:

1. ``test_worker_stops_promptly_when_interrupted_mid_parse`` drives the worker
   directly and verifies that ``requestInterruption()`` stops an in-flight
   parse at the very next record checkpoint.
2. ``test_teardown_worker_stops_after_interruption`` drives a real
   ``CollectionImportActions.teardown()`` with an explicit budget against an
   in-flight worker and verifies that it is reaped without the
   interrupt-timeout path.
3. ``test_default_teardown_requests_interruption_before_wait_and_discards_result``
   verifies the default 5000 ms teardown path requests interruption before
   waiting and does not apply a parse result.
4. ``test_worker_pre_start_interruption_skips_reader`` and
   ``test_teardown_pre_start_interruption_applies_nothing`` cover the worker's
   pre-read interruption check (PYPOST-1265): an interruption requested after
   ``start()`` but before ``run()`` reaches its first check never calls the
   reader.

Synchronization is causal, not timing based (PYPOST-1265): readers are held on
an event that is released only after the real ``requestInterruption()`` call,
so a held reader cannot finish naturally and no wall-clock threshold is
asserted. Outcome signals are counted with ``DirectConnection`` on the worker
thread.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget

from pypost.core.collection_import_lifecycle_policy import ImportTeardownDeadline
from pypost.core.qt.collection_import_parse_worker import (
    CollectionImportParseWorker,
    ReadImportFile,
)
from pypost.models.models import Collection
from pypost.ui.presenters.collection_import_actions import CollectionImportActions
from tests.helpers.collections_tree import FakeRequestManager
from tests.helpers.process_until import process_until

pytestmark = pytest.mark.timeout(30)

_MODULE = "pypost.ui.presenters.collection_import_actions"
_WORKER_LOGGER = "pypost.core.qt.collection_import_parse_worker"
_RESULT_DIALOG = f"{_MODULE}.show_collection_import_result"

_PATH = Path("/dummy/import-cancellation.json")
_RECORD_COUNT = 40
# Bound for every gate/hold event wait. Far above normal latency; a timeout is
# recorded on the double and fails the test instead of hanging it.
_GATE_S = 5.0
_WORKER_WAIT_MS = 5000

# Explicit teardown budget. Since PYPOST-1264 every teardown phase shares this
# one budget. With the held reader it only has to cover one more checkpoint and
# thread exit after the release that follows the real interruption request.
_TEARDOWN_WAIT_IDLE_MS = 1000


class _HeldReader:
    """Cancellation-aware reader that cannot finish while it is held.

    Mirrors ``load_collection_import_candidates`` (keyword ``on_progress``
    called once per record) without the real parser or a file on disk. After
    ``on_progress(hold_at, total)`` returns it sets ``holding`` and waits on
    ``release``, so a test can interrupt a provably in-flight parse whatever
    the runner speed. ``processed`` records every record handed to a checkpoint
    and ``observed`` records the type names of exceptions raised by a checkpoint.
    """

    def __init__(self, hold_at: int = 1, total: int = _RECORD_COUNT) -> None:
        self.hold_at = hold_at
        self.total = total
        self.processed: list[int] = []
        self.observed: list[str] = []
        self.holding = threading.Event()
        self.release = threading.Event()
        self.hold_timed_out = False

    def __call__(
        self, path: Path, *, on_progress: Callable[[int, int], None]
    ) -> tuple[list[Collection], list[str]]:
        assert path == _PATH
        collections: list[Collection] = []
        for record in range(1, self.total + 1):
            self.processed.append(record)
            collections.append(Collection(id=f"c{record}", name=f"C{record}"))
            try:
                on_progress(record, self.total)
            except BaseException as exc:
                self.observed.append(type(exc).__name__)
                raise
            if record == self.hold_at:
                self.holding.set()
                if not self.release.wait(timeout=_GATE_S):
                    self.hold_timed_out = True
        return collections, []


class _RecordingReader:
    """Reader that records every call and returns an empty result."""

    def __init__(self) -> None:
        self.calls: list[Path] = []

    def __call__(
        self, path: Path, *, on_progress: Callable[[int, int], None]
    ) -> tuple[list[Collection], list[str]]:
        self.calls.append(path)
        return [], []


class _GatedWorker(CollectionImportParseWorker):
    """Hold a real running thread at the start of ``run()``.

    The gate only fixes the interleaving between ``start()`` and the first
    production interruption check; the production ``run()`` body executes
    unchanged via ``super().run()``.
    """

    def __init__(self, path: Path, read_import_file: ReadImportFile) -> None:
        super().__init__(path, read_import_file)
        self.entered = threading.Event()
        self.release = threading.Event()
        self.gate_timed_out = False

    def run(self) -> None:
        self.entered.set()
        if not self.release.wait(timeout=_GATE_S):
            self.gate_timed_out = True
        super().run()


class _OutcomeRecorder:
    """Count outcome emissions on the worker thread (``DirectConnection``)."""

    def __init__(self) -> None:
        self.progress: list[tuple[int, int]] = []
        self.cancelled: list[bool] = []
        self.completed: list[tuple[list[Collection], list[str]]] = []
        self.failed: list[object] = []

    def attach(self, worker: CollectionImportParseWorker) -> None:
        direct = Qt.ConnectionType.DirectConnection
        worker.parse_progress.connect(
            lambda done, total: self.progress.append((done, total)), direct
        )
        worker.parse_cancelled.connect(lambda: self.cancelled.append(True), direct)
        worker.parse_completed.connect(
            lambda cols, errors: self.completed.append((cols, errors)), direct
        )
        worker.parse_failed.connect(self.failed.append, direct)


def _release_on_interrupt(
    worker: CollectionImportParseWorker, release: threading.Event
) -> None:
    """Release ``release`` only after the worker's real interruption request."""
    real_request = worker.requestInterruption

    def _request_then_release() -> None:
        real_request()
        release.set()

    worker.requestInterruption = _request_then_release  # type: ignore[method-assign]


def _stop_worker(worker: CollectionImportParseWorker | None) -> None:
    """Defensive cleanup: never leak a running thread into later tests."""
    if worker is None:
        return
    try:
        running = worker.isRunning()
    except RuntimeError:
        running = False
    if running:
        worker.requestInterruption()
        worker.wait(_WORKER_WAIT_MS)


def test_worker_stops_promptly_when_interrupted_mid_parse(qapp: QApplication) -> None:
    """requestInterruption() during parse must stop at the very next checkpoint."""
    reader = _HeldReader(hold_at=1)
    worker = CollectionImportParseWorker(_PATH, reader)
    outcomes = _OutcomeRecorder()
    outcomes.attach(worker)

    worker.start()
    try:
        assert reader.holding.wait(timeout=_GATE_S), "reader never reached its hold point"

        # The reader is held after checkpoint 1, so the parse is provably in flight.
        worker.requestInterruption()
        reader.release.set()
        assert worker.wait(_WORKER_WAIT_MS), "worker did not finish after interruption"

        assert not reader.hold_timed_out
        assert reader.processed == [1, 2], (
            "worker did not stop at the next on_progress checkpoint after "
            "requestInterruption() -- cooperative cancellation was not observed "
            f"promptly (processed={reader.processed}, PYPOST-1229)"
        )
        assert reader.processed[-1] < reader.total
        assert reader.observed == ["CollectionImportCancelled"], (
            "the reader must observe CollectionImportCancelled from its checkpoint"
        )
        assert outcomes.cancelled == [True], "exactly one parse_cancelled emission"
        assert outcomes.completed == [], (
            "parse_completed must NOT be emitted for an interrupted parse -- "
            "if it fired, the worker ran to completion instead of actually "
            "stopping at interruption (PYPOST-1229)"
        )
        assert outcomes.failed == [], (
            "parse_failed must NOT be emitted for an interrupted parse -- "
            "cancellation is not a failure and must not be misreported "
            "through this signal (PYPOST-1229)"
        )
    finally:
        reader.release.set()
        _stop_worker(worker)


def test_teardown_worker_stops_after_interruption(
    qapp: QApplication,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Real CollectionImportActions.teardown() against a real, in-flight worker.

    Covers the PYPOST-1182 "Worker Cancellation on Early Teardown" path:
    ``teardown()`` requests interruption and joins a still-busy worker without
    leaving a background thread running.
    """
    reader = _HeldReader(hold_at=1)
    parent = QWidget()
    actions = CollectionImportActions(
        parent,
        FakeRequestManager([]),
        read_import_file=reader,
        refresh_tree=lambda: None,
        restore_tree_state=lambda: None,
        emit_collections_changed=lambda: None,
    )
    worker: CollectionImportParseWorker | None = None
    worker_finished = threading.Event()
    try:
        actions._start_parse(_PATH)
        worker = actions._worker
        assert worker is not None, "starting a parse must create a real worker"
        worker.finished.connect(worker_finished.set)
        assert reader.holding.wait(timeout=_GATE_S), "reader never reached its hold point"

        outcomes = _OutcomeRecorder()
        outcomes.attach(worker)
        _release_on_interrupt(worker, reader.release)

        # A non-cooperating worker would emit parse_completed; patch the result
        # dialog so such a regression fails cleanly instead of blocking on it.
        with patch(_RESULT_DIALOG) as result_dialog, caplog.at_level(
            logging.DEBUG, logger=_MODULE
        ):
            actions.teardown(timeout_ms=_TEARDOWN_WAIT_IDLE_MS)
        messages = [r.message for r in caplog.records]

        assert worker_finished.is_set(), "worker must finish before teardown returns"
        assert actions._worker is None, "teardown must reap the worker reference"
        assert not reader.hold_timed_out
        assert outcomes.cancelled == [True], "exactly one parse_cancelled emission"
        assert outcomes.completed == []
        assert outcomes.failed == []
        assert reader.processed == [1, 2], (
            "the worker must stop at the checkpoint right after teardown's "
            f"interruption request (processed={reader.processed})"
        )
        assert reader.processed[-1] < reader.total
        assert reader.observed == ["CollectionImportCancelled"]
        result_dialog.assert_not_called()
        assert any("collection_import_worker_interrupted" in m for m in messages), (
            "teardown() should log collection_import_worker_interrupted -- "
            "i.e. the worker actually stopped within the final join once "
            "interruption was requested"
        )
        assert any(
            "collection_import_parse_cancelled from_state=parsing" in m
            for m in messages
        ), "the GUI terminal cancellation event should identify the prior parse state"
        assert (
            sum(m.startswith("collection_import_parse_cancelled ") for m in messages) == 1
        ), "the presenter must handle exactly one cancellation"
        assert not any("collection_import_worker_interrupt_timeout" in m for m in messages), (
            "teardown() should NOT hit the final join timeout path -- that "
            "path means the worker ignored requestInterruption() and kept "
            "running (PYPOST-1182 / PYPOST-1229)"
        )
    finally:
        reader.release.set()
        _stop_worker(worker)


def test_default_teardown_requests_interruption_before_wait_and_discards_result(
    qapp: QApplication,
) -> None:
    """Default teardown interrupts before waiting and applies no parse result."""
    reader = _HeldReader(hold_at=1)
    parent = QWidget()
    refresh_tree = MagicMock()
    restore_tree_state = MagicMock()
    emit_collections_changed = MagicMock()
    actions = CollectionImportActions(
        parent,
        FakeRequestManager([]),
        read_import_file=reader,
        refresh_tree=refresh_tree,
        restore_tree_state=restore_tree_state,
        emit_collections_changed=emit_collections_changed,
    )
    worker: CollectionImportParseWorker | None = None
    worker_finished = threading.Event()
    wait_observations: list[tuple[int, bool]] = []
    try:
        actions._start_parse(_PATH)
        worker = actions._worker
        assert worker is not None, "starting a parse must create a real worker"
        worker.finished.connect(worker_finished.set)
        assert reader.holding.wait(timeout=_GATE_S), "reader never reached its hold point"

        outcomes = _OutcomeRecorder()
        outcomes.attach(worker)
        _release_on_interrupt(worker, reader.release)

        # Teardown's wait-idle phase shares the teardown deadline (PYPOST-1264),
        # so observe the private phase and record the deadline's budget.
        real_wait_idle_until = actions._wait_idle_until

        def _observe_wait(deadline: ImportTeardownDeadline) -> bool:
            wait_observations.append(
                (deadline.budget_ms, worker.isInterruptionRequested())
            )
            return real_wait_idle_until(deadline)

        actions._wait_idle_until = _observe_wait  # type: ignore[method-assign]
        with patch(_RESULT_DIALOG) as result_dialog:
            assert actions.teardown() is True

        assert wait_observations == [(5000, True)], (
            "default teardown must request interruption before entering wait_idle"
        )
        assert worker_finished.is_set(), "worker must finish before teardown returns"
        assert actions._worker is None
        assert not reader.hold_timed_out
        assert outcomes.cancelled == [True], "exactly one parse_cancelled emission"
        assert outcomes.completed == []
        assert outcomes.failed == []
        assert reader.processed == [1, 2], (
            "the worker must stop at the checkpoint right after teardown's "
            f"interruption request (processed={reader.processed})"
        )
        assert reader.processed[-1] < reader.total
        assert reader.observed == ["CollectionImportCancelled"]
        refresh_tree.assert_not_called()
        restore_tree_state.assert_not_called()
        emit_collections_changed.assert_not_called()
        result_dialog.assert_not_called()
    finally:
        reader.release.set()
        _stop_worker(worker)


def test_worker_pre_start_interruption_skips_reader(
    qapp: QApplication,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """An interruption seen by the pre-read check must never call the reader."""
    reader = _RecordingReader()
    worker = _GatedWorker(_PATH, reader)
    outcomes = _OutcomeRecorder()
    outcomes.attach(worker)

    try:
        with caplog.at_level(logging.INFO, logger=_WORKER_LOGGER):
            worker.start()
            assert worker.entered.wait(timeout=_GATE_S), "worker never entered run()"
            # The thread is running and held before the production check.
            worker.requestInterruption()
            worker.release.set()
            assert worker.wait(_WORKER_WAIT_MS), "gated worker did not finish"

        assert not worker.gate_timed_out
        assert reader.calls == [], (
            "the pre-read interruption check must stop the worker before the "
            f"reader is called (reader calls={reader.calls})"
        )
        assert outcomes.progress == []
        assert outcomes.cancelled == [True], "exactly one parse_cancelled emission"
        assert outcomes.completed == []
        assert outcomes.failed == []
        cancelled_logs = [
            r for r in caplog.records
            if r.name == _WORKER_LOGGER
            and r.message.startswith("collection_import_parse_worker_cancelled")
        ]
        assert len(cancelled_logs) == 1
    finally:
        worker.release.set()
        _stop_worker(worker)


def test_teardown_pre_start_interruption_applies_nothing(qapp: QApplication) -> None:
    """Closing right after starting an import cancels before the reader runs."""
    reader = _RecordingReader()
    manager = FakeRequestManager([])
    refresh_tree = MagicMock()
    restore_tree_state = MagicMock()
    emit_collections_changed = MagicMock()
    parent = QWidget()
    actions = CollectionImportActions(
        parent,
        manager,
        read_import_file=reader,
        refresh_tree=refresh_tree,
        restore_tree_state=restore_tree_state,
        emit_collections_changed=emit_collections_changed,
    )
    started: CollectionImportParseWorker | None = None
    worker_finished = threading.Event()
    try:
        with patch(f"{_MODULE}.CollectionImportParseWorker", _GatedWorker):
            actions._start_parse(_PATH)
        # Capture the started thread before the type assert so cleanup can stop it.
        started = actions._worker
        assert isinstance(started, _GatedWorker), "teardown test needs the gated worker"
        worker = started
        worker.finished.connect(worker_finished.set)
        assert worker.entered.wait(timeout=_GATE_S), "worker never entered run()"

        outcomes = _OutcomeRecorder()
        outcomes.attach(worker)
        _release_on_interrupt(worker, worker.release)

        with patch(_RESULT_DIALOG) as result_dialog:
            assert actions.teardown(timeout_ms=_TEARDOWN_WAIT_IDLE_MS) is True

        assert not worker.gate_timed_out
        assert reader.calls == [], (
            "teardown right after start must cancel before the reader is called "
            f"(reader calls={reader.calls})"
        )
        assert outcomes.progress == []
        assert outcomes.cancelled == [True], "exactly one parse_cancelled emission"
        assert outcomes.completed == []
        assert outcomes.failed == []
        refresh_tree.assert_not_called()
        restore_tree_state.assert_not_called()
        emit_collections_changed.assert_not_called()
        result_dialog.assert_not_called()
        assert manager.collections == []
        assert worker_finished.is_set(), "worker must finish before teardown returns"
        assert actions._worker is None
        assert not actions.is_busy()
    finally:
        if isinstance(started, _GatedWorker):
            started.release.set()
        _stop_worker(started)


def test_final_publication_guard_discards_result_after_last_checkpoint(
    qapp: QApplication,
) -> None:
    """A final-boundary interruption must not reach presenter result application."""
    final_checkpoint_returned = threading.Event()
    release_reader = threading.Event()

    def reader(
        path: Path,
        on_progress: Callable[[int, int], None] | None = None,
    ) -> tuple[list[Collection], list[str]]:
        assert path == _PATH
        assert on_progress is not None
        on_progress(1, 1)
        final_checkpoint_returned.set()
        release_reader.wait(timeout=5.0)
        return [Collection(id="final", name="Final")], []

    parent = QWidget()
    actions = CollectionImportActions(
        parent,
        FakeRequestManager([]),
        read_import_file=reader,
        refresh_tree=MagicMock(),
        restore_tree_state=MagicMock(),
        emit_collections_changed=MagicMock(),
    )
    worker: CollectionImportParseWorker | None = None
    worker_finished = threading.Event()
    completed_signals: list[None] = []
    cancelled_signals: list[None] = []
    try:
        with patch.object(
            actions,
            "_on_parse_completed",
            wraps=actions._on_parse_completed,
        ) as on_parse_completed, patch.object(
            actions, "_finish_import"
        ) as finish_import:
            actions._start_parse(_PATH)
            worker = actions._worker
            assert worker is not None, "starting a parse must create a real worker"
            worker.finished.connect(worker_finished.set)
            worker.parse_completed.connect(
                lambda *_args: completed_signals.append(None)
            )
            worker.parse_cancelled.connect(lambda: cancelled_signals.append(None))

            process_until(final_checkpoint_returned.is_set, timeout_ms=5000)
            worker.requestInterruption()
            release_reader.set()

            process_until(
                lambda: not actions.is_busy() or on_parse_completed.called,
                timeout_ms=5000,
            )
            process_until(worker_finished.is_set, timeout_ms=5000)

            assert worker_finished.is_set()
            assert completed_signals == []
            assert cancelled_signals == [None]
            on_parse_completed.assert_not_called()
            finish_import.assert_not_called()
    finally:
        release_reader.set()
        if worker is not None:
            try:
                running = worker.isRunning()
            except RuntimeError:
                running = False
            if running:
                worker.requestInterruption()
                worker.wait(5000)
