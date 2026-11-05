"""Library operation worker cooperative interrupt contract (PYPOST-1324).

Collection-import teardown must call library ``cancel()`` (CTS + interruption)
then ``wait(bounded(final_join_ms))``. A cancel-aware operation observes the
token and stops cleanly; a cancel-ignoring stuck op still returns unclean within
a loose ``< 2B`` wall-time bound.

* Test A — spy library worker: ``cancel()`` before wait, wait ``<= final_join_ms``
* Test B — real worker + cancel-aware op: observes token, clean teardown, no late
  completed delivery into the apply hook
* Unclean guard — cancel-ignoring stuck op still returns unclean within ``< 2B``
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from PySide6.QtWidgets import QWidget

from pypost.core.cancellation import OperationCancelledError
from pypost.core.collection_import_lifecycle_policy import (
    DEFAULT_COLLECTION_IMPORT_LIFECYCLE_POLICY,
)
from pypost.core.collection_import_state import CollectionImportState
from pypost.models.models import Collection
from pypost.ui.presenters.collection_import_actions import CollectionImportActions
from tests.helpers.collections_tree import FakeRequestManager

pytestmark = pytest.mark.timeout(30)

_FINAL_JOIN_MS = DEFAULT_COLLECTION_IMPORT_LIFECYCLE_POLICY.final_join_ms
_RELEASE_TIMEOUT_S = 5.0
_CLEANUP_JOIN_MS = 2000
# Test B: cancel-honoring path must finish well under a full join-only budget burn.
_HONORING_ELAPSED_LIMIT_MS = 400


class _SpySignal:
    """Signal stand-in whose ``disconnect`` is a no-op."""

    def disconnect(self, *_args: Any) -> None:
        return None


class FakeClock:
    """Monotonic fake clock in seconds that moves only when advanced."""

    def __init__(self) -> None:
        self._now = 1000.0

    def __call__(self) -> float:
        return self._now

    def advance(self, ms: int) -> None:
        self._now += ms / 1000.0


class _SpyLibraryWorker:
    """Library worker stand-in that records ``cancel`` / interrupt / ``wait`` order."""

    def __init__(self, on_wait: Callable[[int], None]) -> None:
        self._on_wait = on_wait
        self.events: list[str] = []
        self.cancels = 0
        self.interruptions = 0
        self.waits: list[int] = []
        self.deleted = 0
        self.operation_completed = _SpySignal()
        self.operation_failed = _SpySignal()
        self.operation_cancelled = _SpySignal()
        self.finished = _SpySignal()

    def isRunning(self) -> bool:  # noqa: N802 - mirrors QThread API
        return True

    def cancel(self) -> None:
        self.cancels += 1
        self.events.append("cancel")

    def requestInterruption(self) -> None:  # noqa: N802 - mirrors QThread API
        self.interruptions += 1
        self.events.append("requestInterruption")

    def deleteLater(self) -> None:  # noqa: N802 - mirrors QThread API
        self.deleted += 1

    def wait(self, ms: int) -> bool:
        self.waits.append(ms)
        self.events.append(f"wait:{ms}")
        self._on_wait(ms)
        return False


def _make_actions(parent: QWidget, **extra: Any) -> CollectionImportActions:
    def _unused_reader(
        _path: Path, /, *, on_progress: Callable[[int, int], None]
    ) -> tuple[list[Collection], list[str]]:
        return [], []

    return CollectionImportActions(
        parent,
        FakeRequestManager([]),
        read_import_file=_unused_reader,
        refresh_tree=lambda: None,
        restore_tree_state=lambda: None,
        emit_collections_changed=lambda: None,
        **extra,
    )


def test_teardown_calls_library_cancel_then_bounded_final_join(qapp) -> None:
    """Test A: P3 must call library ``cancel()`` then ``wait(<= final_join_ms)``."""
    clock = FakeClock()
    budget_ms = 300
    parent = QWidget()
    actions = _make_actions(parent, clock=clock)
    library_spy = _SpyLibraryWorker(clock.advance)
    # IDLE skips P0/P1 and any file join so P3 sees the full budget as remaining.
    actions._state = CollectionImportState.IDLE
    actions._library_worker = library_spy  # type: ignore[assignment]

    clean = actions.teardown(timeout_ms=budget_ms)

    assert library_spy.cancels >= 1, (
        "teardown must call library worker cancel() before joining "
        f"(events={library_spy.events})"
    )
    assert library_spy.waits, "teardown must join the library worker"
    wait_ms = library_spy.waits[0]
    assert wait_ms <= _FINAL_JOIN_MS, (
        f"P3 library wait {wait_ms} ms must be <= final_join_ms {_FINAL_JOIN_MS} ms "
        f"(not full remaining budget {budget_ms} ms); events={library_spy.events}"
    )
    assert wait_ms <= budget_ms
    cancel_idx = library_spy.events.index("cancel")
    wait_idx = next(
        i for i, event in enumerate(library_spy.events) if event.startswith("wait:")
    )
    assert cancel_idx < wait_idx, (
        f"cancel() must precede wait(); events={library_spy.events}"
    )
    assert clean is False, "spy that times out its join must yield unclean"


def test_cancel_aware_library_op_stops_cleanly_within_bounded_teardown(qapp) -> None:
    """Test B: cancel-aware op observes token; teardown is clean and bounded."""
    entered = threading.Event()
    cancelled_observed = threading.Event()
    release = threading.Event()
    completed_results: list[Any] = []
    budget_ms = 1000

    def _cancel_aware_op(
        *, cancellation_token: Any | None = None
    ) -> str:
        entered.set()
        deadline = time.monotonic() + _RELEASE_TIMEOUT_S
        while time.monotonic() < deadline:
            if cancellation_token is not None:
                try:
                    cancellation_token.throw_if_cancellation_requested()
                except OperationCancelledError:
                    cancelled_observed.set()
                    raise
            if release.wait(timeout=0.05):
                return "done"
        return "timeout"

    parent = QWidget()
    actions = _make_actions(parent)
    actions._state = CollectionImportState.PREPARING
    threads: list[Any] = []
    deferred_deletes: list[Callable[[], None]] = []

    def _defer_delete(worker: Any) -> None:
        real_delete = worker.deleteLater
        deferred_deletes.append(real_delete)
        worker.deleteLater = lambda: None

    try:
        actions._start_library_operation(_cancel_aware_op, completed_results.append)
        library_worker = actions._library_worker
        assert library_worker is not None, "library worker must be started"
        threads.append(library_worker)
        _defer_delete(library_worker)

        assert entered.wait(timeout=_RELEASE_TIMEOUT_S), (
            "library operation never entered its cancel-aware loop"
        )

        actions_logger = logging.getLogger(CollectionImportActions.__module__)
        logger_was_disabled = actions_logger.disabled
        actions_logger.disabled = True
        try:
            started = time.perf_counter()
            clean = actions.teardown(timeout_ms=budget_ms)
            elapsed_ms = (time.perf_counter() - started) * 1000.0
        finally:
            actions_logger.disabled = logger_was_disabled

        assert cancelled_observed.is_set(), (
            "cancel-aware library operation must observe CancellationToken during "
            "teardown"
        )
        assert clean is True, (
            "honoring cancel within final_join must yield a clean teardown, "
            f"got clean={clean} elapsed_ms={elapsed_ms:.0f}"
        )
        assert completed_results == [], (
            "teardown must not deliver operation_completed into apply hooks after "
            f"cancel; got {completed_results!r}"
        )
        assert elapsed_ms < _HONORING_ELAPSED_LIMIT_MS, (
            f"teardown(timeout_ms={budget_ms}) took {elapsed_ms:.0f} ms; "
            f"cancel-honoring path must stay under {_HONORING_ELAPSED_LIMIT_MS} ms "
            f"(not burn the full remaining join-only budget)"
        )
        assert elapsed_ms < DEFAULT_COLLECTION_IMPORT_LIFECYCLE_POLICY.teardown_budget_ms
    finally:
        release.set()
        for thread in threads:
            thread.wait(_CLEANUP_JOIN_MS)
        for real_delete in deferred_deletes:
            real_delete()


def test_cancel_ignoring_library_op_teardown_stays_within_caller_budget(qapp) -> None:
    """Unclean guard: stuck op that ignores cancel still returns within ``< 2B``."""
    entered = threading.Event()
    release = threading.Event()
    budget_ms = 300

    def _stuck_library_op(*, cancellation_token: Any | None = None) -> str:
        del cancellation_token  # intentionally ignore cooperative cancel
        entered.set()
        release.wait(timeout=_RELEASE_TIMEOUT_S)
        return "done"

    parent = QWidget()
    actions = _make_actions(parent)
    actions._state = CollectionImportState.PREPARING
    threads: list[Any] = []
    deferred_deletes: list[Callable[[], None]] = []

    def _defer_delete(worker: Any) -> None:
        real_delete = worker.deleteLater
        deferred_deletes.append(real_delete)
        worker.deleteLater = lambda: None

    try:
        actions._start_library_operation(_stuck_library_op, lambda _result: None)
        library_worker = actions._library_worker
        assert library_worker is not None, "library worker must be started"
        threads.append(library_worker)
        _defer_delete(library_worker)

        assert entered.wait(timeout=_RELEASE_TIMEOUT_S), (
            "library operation never entered the stuck body"
        )

        actions_logger = logging.getLogger(CollectionImportActions.__module__)
        logger_was_disabled = actions_logger.disabled
        actions_logger.disabled = True
        try:
            started = time.perf_counter()
            clean = actions.teardown(timeout_ms=budget_ms)
            elapsed_ms = (time.perf_counter() - started) * 1000.0
        finally:
            actions_logger.disabled = logger_was_disabled

        assert clean is False, (
            "cancel-ignoring stuck library op past the budget must yield unclean"
        )
        limit_ms = 2 * budget_ms
        assert elapsed_ms < limit_ms, (
            f"teardown(timeout_ms={budget_ms}) took {elapsed_ms:.0f} ms >= "
            f"loose bound {limit_ms} ms"
        )
    finally:
        release.set()
        for thread in threads:
            thread.wait(_CLEANUP_JOIN_MS)
        for real_delete in deferred_deletes:
            real_delete()
