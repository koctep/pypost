"""Reproduction tests for cooperative worker cancellation (PYPOST-1229).

These tests cover cooperative cancellation in ``CollectionImportParseWorker``
and the ``CollectionImportActions.teardown()`` lifecycle. The first two tests
were originally red reproductions for PYPOST-1229 and now verify the corrected
behavior.

Two scenarios are covered here:

1. ``test_worker_stops_promptly_when_interrupted_mid_parse`` drives the
   ``CollectionImportParseWorker`` directly and verifies that
   ``requestInterruption()`` stops an in-flight parse.
2. ``test_teardown_worker_stops_after_interruption`` drives a real
   ``CollectionImportActions.teardown()`` against the same slow worker and
   verifies that the worker is reaped without the interrupt-timeout path.
3. ``test_default_teardown_requests_interruption_before_wait_and_discards_result``
   verifies the default 5000 ms teardown path requests interruption before
   waiting and does not apply a queued parse result.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication, QWidget

from pypost.core.qt.collection_import_parse_worker import CollectionImportParseWorker
from pypost.models.models import Collection
from pypost.ui.presenters.collection_import_actions import CollectionImportActions
from tests.helpers.collections_tree import FakeRequestManager
from tests.helpers.process_until import process_until

pytestmark = pytest.mark.timeout(30)

_MODULE = "pypost.ui.presenters.collection_import_actions"

_PATH = Path("/dummy/import-cancellation.json")
_RECORD_COUNT = 40
_RECORD_DELAY_S = 0.05  # ~2s total run time if never interrupted
_WAIT_AFTER_INTERRUPT_MS = 300  # well under the ~2s full run


def _slow_reader(
    path: Path,
    on_progress: Callable[[int, int], None] | None = None,
) -> tuple[list[Collection], list[str]]:
    """Fake read_import_file: many records, each with a small delay.

    Mirrors the shape of ``load_collection_import_candidates`` (per-record
    ``on_progress(done, total)`` callback) without depending on the real
    parser or any file on disk.
    """
    assert path == _PATH
    collections: list[Collection] = []
    for i in range(1, _RECORD_COUNT + 1):
        time.sleep(_RECORD_DELAY_S)
        collections.append(Collection(id=f"c{i}", name=f"C{i}"))
        if on_progress is not None:
            on_progress(i, _RECORD_COUNT)
    return collections, []


def test_worker_stops_promptly_when_interrupted_mid_parse(qapp: QApplication) -> None:
    """requestInterruption() during parse must stop the worker promptly."""
    worker = CollectionImportParseWorker(_PATH, _slow_reader)

    first_progress = threading.Event()
    worker.parse_progress.connect(lambda done, total: first_progress.set())

    completed_flag = threading.Event()
    failed_flag = threading.Event()
    worker.parse_completed.connect(lambda *_args: completed_flag.set())
    worker.parse_failed.connect(lambda *_args: failed_flag.set())

    worker.start()
    try:
        process_until(lambda: first_progress.is_set(), timeout_ms=5000)

        # Interrupt as soon as we've observed the worker is actually mid-parse.
        worker.requestInterruption()
        stopped_promptly = worker.wait(_WAIT_AFTER_INTERRUPT_MS)

        assert stopped_promptly, (
            "worker did not stop within "
            f"{_WAIT_AFTER_INTERRUPT_MS}ms of requestInterruption() -- "
            "cooperative cancellation was not observed at the next "
            "on_progress checkpoint (PYPOST-1229)"
        )
        assert not completed_flag.is_set(), (
            "parse_completed must NOT be emitted for an interrupted parse -- "
            "if it fired, the worker ran to completion instead of actually "
            "stopping at interruption (PYPOST-1229)"
        )
        assert not failed_flag.is_set(), (
            "parse_failed must NOT be emitted for an interrupted parse -- "
            "cancellation is not a failure and must not be misreported "
            "through this signal (PYPOST-1229)"
        )
    finally:
        # Regardless of the assertion outcome, don't leak a running thread
        # into later tests.
        if worker.isRunning():
            worker.requestInterruption()
            worker.wait(5000)


# Keep a short teardown budget so this regression remains focused on an
# actually in-flight worker rather than a naturally completed parse. The
# worker is interrupted before wait_idle() starts polling.
_TEARDOWN_WAIT_IDLE_MS = 150


def test_teardown_worker_stops_after_interruption(
    qapp: QApplication,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Real CollectionImportActions.teardown() against a real, slow worker.

    Covers the PYPOST-1182 "Worker Cancellation on Early Teardown" path:
    ``teardown()`` requests interruption and joins a still-busy worker without
    leaving a background thread running.
    """
    parent = QWidget()
    actions = CollectionImportActions(
        parent,
        FakeRequestManager([]),
        read_import_file=_slow_reader,
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

        first_progress = threading.Event()
        worker.parse_progress.connect(lambda done, total: first_progress.set())
        process_until(lambda: first_progress.is_set(), timeout_ms=5000)

        with caplog.at_level(logging.DEBUG, logger=_MODULE):
            actions.teardown(timeout_ms=_TEARDOWN_WAIT_IDLE_MS)
        messages = [r.message for r in caplog.records]

        assert worker_finished.is_set(), "worker must finish before teardown returns"
        assert actions._worker is None, "teardown must reap the worker reference"
        assert any("collection_import_worker_interrupted" in m for m in messages), (
            "teardown() should log collection_import_worker_interrupted -- "
            "i.e. the worker actually stopped within wait(100) once "
            "interruption was requested"
        )
        assert any(
            "collection_import_parse_cancelled from_state=parsing" in m
            for m in messages
        ), "the GUI terminal cancellation event should identify the prior parse state"
        assert not any("collection_import_worker_interrupt_timeout" in m for m in messages), (
            "teardown() should NOT hit the wait(100) timeout path -- that "
            "path means the worker ignored requestInterruption() and kept "
            "running (PYPOST-1182 / PYPOST-1229)"
        )
    finally:
        if worker is not None:
            try:
                running = worker.isRunning()
            except RuntimeError:
                running = False
            if running:
                worker.requestInterruption()
                worker.wait(5000)


def test_default_teardown_requests_interruption_before_wait_and_discards_result(
    qapp: QApplication,
) -> None:
    """Default teardown interrupts before waiting and applies no parse result."""
    parent = QWidget()
    refresh_tree = MagicMock()
    restore_tree_state = MagicMock()
    emit_collections_changed = MagicMock()
    actions = CollectionImportActions(
        parent,
        FakeRequestManager([]),
        read_import_file=_slow_reader,
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

        first_progress = threading.Event()
        worker.parse_progress.connect(lambda done, total: first_progress.set())
        process_until(lambda: first_progress.is_set(), timeout_ms=5000)

        real_wait_idle = actions.wait_idle

        def _observe_wait(timeout_ms: int) -> bool:
            wait_observations.append(
                (timeout_ms, worker.isInterruptionRequested())
            )
            return real_wait_idle(timeout_ms)

        actions.wait_idle = _observe_wait  # type: ignore[method-assign]
        with patch(
            "pypost.ui.presenters.collection_import_actions.show_collection_import_result"
        ) as result_dialog:
            assert actions.teardown() is True

        assert wait_observations == [(5000, True)], (
            "default teardown must request interruption before entering wait_idle"
        )
        assert worker_finished.is_set(), "worker must finish before teardown returns"
        assert actions._worker is None
        refresh_tree.assert_not_called()
        restore_tree_state.assert_not_called()
        emit_collections_changed.assert_not_called()
        result_dialog.assert_not_called()
    finally:
        if worker is not None:
            try:
                running = worker.isRunning()
            except RuntimeError:
                running = False
            if running:
                worker.requestInterruption()
                worker.wait(5000)


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
