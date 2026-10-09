"""Failing repro: collection import teardown must respect the caller budget (PYPOST-1264).

``CollectionImportActions.teardown(timeout_ms)`` runs its phases one after another and
gives each phase its own budget: the wait-idle phase (P1) can use the full budget, the
post-disconnect file-worker join (P2) is a fixed ``wait(100)`` even when the budget is
exhausted, and the library-worker join (P3) gets the full budget again. The worst case is
about ``2 * timeout_ms + 100`` ms, which breaks the caller budget (DoD 3).

The tests here assert the desired shared-deadline behaviour:

* Test A (``test_teardown_requested_waits_fit_caller_budget``): spy workers whose
  ``wait(ms)`` really sleeps; the requested waits must sum to at most the budget, P2 must
  not exceed the final join limit, and an exhausted budget issues only ``wait(0)`` probes.
  Built with today's constructor signature, so it fails by assertion, not by error.
* Test B (``test_teardown_wait_arithmetic_with_fake_clock``): exact P2/P3 values against
  an injected fake clock (``clock=`` keyword, the designed test seam).
* A loose real-thread guard (``test_teardown_real_threads_stay_within_loose_bound``):
  both workers blocked; wall time must stay well under the old ``2B + 100`` ms behaviour.
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

from pypost.core.collection_import_state import CollectionImportState
from pypost.models.models import Collection
from pypost.ui.presenters.collection_import_actions import CollectionImportActions
from tests.helpers.collections_tree import FakeRequestManager

pytestmark = pytest.mark.timeout(30)

_PATH = Path("/tmp/import.json")
# Step 3 local constant; Step 4 switches it to the policy ``final_join_ms`` field.
_FINAL_JOIN_MS = 100
# Bounded release wait for blocked fake reader / library operation (seconds).
_RELEASE_TIMEOUT_S = 5.0
# Bounded join for real threads in cleanup (ms).
_CLEANUP_JOIN_MS = 2000


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


class _SpyWorker:
    """Worker stand-in that stays running and records every ``wait(ms)`` call.

    ``on_wait`` lets the test decide how time passes during a join that times out:
    a real ``time.sleep`` (test A) or a fake clock advance (test B).
    """

    def __init__(self, on_wait: Callable[[int], None]) -> None:
        self._on_wait = on_wait
        self.waits: list[int] = []
        self.interruptions = 0
        self.deleted = 0
        self.parse_progress = _SpySignal()
        self.parse_completed = _SpySignal()
        self.parse_failed = _SpySignal()
        self.parse_cancelled = _SpySignal()
        self.operation_completed = _SpySignal()
        self.operation_failed = _SpySignal()
        self.finished = _SpySignal()

    def isRunning(self) -> bool:  # noqa: N802 - mirrors QThread API
        return True

    def requestInterruption(self) -> None:  # noqa: N802 - mirrors QThread API
        self.interruptions += 1

    def deleteLater(self) -> None:  # noqa: N802 - mirrors QThread API
        self.deleted += 1

    def wait(self, ms: int) -> bool:
        self.waits.append(ms)
        self._on_wait(ms)
        return False


def _real_sleep(ms: int) -> None:
    # Bounded: every budget in these tests is <= 300 ms.
    time.sleep(ms / 1000.0)


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


def _install_spies(
    actions: CollectionImportActions, on_wait: Callable[[int], None]
) -> tuple[_SpyWorker, _SpyWorker]:
    file_spy = _SpyWorker(on_wait)
    library_spy = _SpyWorker(on_wait)
    # IDLE state skips P0/P1, so teardown goes straight to P2 (file) and P3 (library).
    actions._state = CollectionImportState.IDLE
    actions._worker = file_spy  # type: ignore[assignment]
    actions._library_worker = library_spy  # type: ignore[assignment]
    return file_spy, library_spy


@pytest.mark.parametrize("budget_ms", [300, 50, 0])
def test_teardown_requested_waits_fit_caller_budget(qapp, budget_ms: int) -> None:
    """Test A: requested waits sum to <= B, P2 <= final join, B=0 issues only wait(0)."""
    parent = QWidget()
    actions = _make_actions(parent)
    file_spy, library_spy = _install_spies(actions, _real_sleep)

    clean = actions.teardown(timeout_ms=budget_ms)

    all_waits = file_spy.waits + library_spy.waits
    assert sum(all_waits) <= budget_ms, (
        f"teardown requested waits summing to {sum(all_waits)} ms > caller budget "
        f"{budget_ms} ms (P2 file waits={file_spy.waits}, "
        f"P3 library waits={library_spy.waits})"
    )
    assert file_spy.waits and all(w <= _FINAL_JOIN_MS for w in file_spy.waits), (
        f"P2 file-worker join {file_spy.waits} must be <= final join {_FINAL_JOIN_MS} ms"
    )
    if budget_ms == 0:
        assert all(w == 0 for w in all_waits), (
            f"exhausted budget must issue only wait(0) probes, got {all_waits}"
        )
        assert clean is False, "exhausted budget with live workers must be unclean"


@pytest.mark.parametrize(
    ("budget_ms", "expected_p2", "expected_p3"),
    [(300, 100, 200), (50, 50, 0), (0, 0, 0)],
)
def test_teardown_wait_arithmetic_with_fake_clock(
    qapp, budget_ms: int, expected_p2: int, expected_p3: int
) -> None:
    """Test B: exact P2 = min(final join, remaining), P3 = remaining (fake clock seam)."""
    clock = FakeClock()
    parent = QWidget()
    actions = _make_actions(parent, clock=clock)
    file_spy, library_spy = _install_spies(actions, clock.advance)

    clean = actions.teardown(timeout_ms=budget_ms)

    assert file_spy.waits == [expected_p2], (
        f"P2 file-worker join {file_spy.waits} != [min({_FINAL_JOIN_MS}, remaining)]"
        f" = [{expected_p2}]"
    )
    assert library_spy.waits == [expected_p3], (
        f"P3 library join {library_spy.waits} != [remaining] = [{expected_p3}]"
    )
    assert sum(file_spy.waits + library_spy.waits) <= budget_ms
    assert clean is False, "live workers past their joins must yield an unclean result"


@pytest.mark.parametrize("budget_ms", [300, 0])
def test_teardown_real_threads_stay_within_loose_bound(qapp, budget_ms: int) -> None:
    """Loose guard: both real workers blocked; elapsed < 2B (B=300) or < 100 ms (B=0)."""
    reader_release = threading.Event()
    library_release = threading.Event()
    reader_entered = threading.Event()
    library_entered = threading.Event()

    def _stuck_reader(
        _path: Path, /, *, on_progress: Callable[[int, int], None]
    ) -> tuple[list[Collection], list[str]]:
        # A reader stuck in I/O: ignores cancellation until released.
        reader_entered.set()
        reader_release.wait(timeout=_RELEASE_TIMEOUT_S)
        return [], []

    def _stuck_library_op() -> bool:
        library_entered.set()
        return library_release.wait(timeout=_RELEASE_TIMEOUT_S)

    parent = QWidget()
    actions = CollectionImportActions(
        parent,
        FakeRequestManager([]),
        read_import_file=_stuck_reader,
        refresh_tree=lambda: None,
        restore_tree_state=lambda: None,
        emit_collections_changed=lambda: None,
    )
    threads: list[Any] = []
    deferred_deletes: list[Callable[[], None]] = []

    def _defer_delete(worker: Any) -> None:
        # Keep the QThread alive until it is released and joined in ``finally``.
        real_delete = worker.deleteLater
        deferred_deletes.append(real_delete)
        worker.deleteLater = lambda: None

    try:
        actions._start_parse(_PATH)
        parse_worker = actions._worker
        assert parse_worker is not None, "parse worker must be started"
        threads.append(parse_worker)
        _defer_delete(parse_worker)

        actions._start_library_operation(_stuck_library_op, lambda _result: None)
        library_worker = actions._library_worker
        assert library_worker is not None, "library worker must be started"
        threads.append(library_worker)
        _defer_delete(library_worker)

        # Both workers must be blocked inside their work before teardown runs;
        # otherwise P0 interruption can pre-empt the reader and skip P2.
        assert reader_entered.wait(timeout=_RELEASE_TIMEOUT_S), (
            "parse worker never entered the stuck reader"
        )
        assert library_entered.wait(timeout=_RELEASE_TIMEOUT_S), (
            "library worker never entered the stuck operation"
        )

        # Under parallel ``make test`` the elapsed time was dominated by pytest live
        # logging (``log_cli_level=WARNING``) of teardown's WARNING records, not by
        # teardown itself (up to ~400 ms per record under load). Keep log emission out
        # of this timed window only by disabling the actions logger for the call and
        # restoring it in ``finally``; log content is asserted by other tests.
        actions_logger = logging.getLogger(CollectionImportActions.__module__)
        logger_was_disabled = actions_logger.disabled
        actions_logger.disabled = True
        try:
            started = time.perf_counter()
            clean = actions.teardown(timeout_ms=budget_ms)
            elapsed_ms = (time.perf_counter() - started) * 1000.0
        finally:
            actions_logger.disabled = logger_was_disabled

        assert clean is False, "blocked workers past the budget must yield unclean"
        limit_ms = 2 * budget_ms if budget_ms > 0 else 100
        assert elapsed_ms < limit_ms, (
            f"teardown(timeout_ms={budget_ms}) took {elapsed_ms:.0f} ms >= "
            f"loose bound {limit_ms} ms"
        )
    finally:
        reader_release.set()
        library_release.set()
        for thread in threads:
            thread.wait(_CLEANUP_JOIN_MS)
        for real_delete in deferred_deletes:
            real_delete()
