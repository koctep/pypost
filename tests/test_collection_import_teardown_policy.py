"""Collection import teardown follows the lifecycle policy and one deadline (PYPOST-1264).

Deterministic: spy workers and a fake clock, no real threads and no wall-time asserts.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QWidget

from pypost.core.collection_import_lifecycle_policy import CollectionImportLifecyclePolicy
from pypost.core.collection_import_state import CollectionImportState
from pypost.core.metrics_registry import MetricsRegistry
from pypost.models.models import Collection
from pypost.ui.presenters.collection_import_actions import CollectionImportActions
from pypost.ui.presenters.collections_presenter import CollectionsPresenter
from tests.helpers.collections_tree import (
    FakeMetrics,
    FakeRequestManager,
    FakeStateManager,
)

pytestmark = pytest.mark.timeout(30)

_MODULE = "pypost.ui.presenters.collection_import_actions"


class FakeClock:
    """Fake monotonic clock (seconds); optionally ticks ``tick_ms`` on every read."""

    def __init__(self, tick_ms: float = 0.0) -> None:
        self._now = 1000.0
        self.tick_ms = tick_ms

    def __call__(self) -> float:
        now = self._now
        self._now += self.tick_ms / 1000.0
        return now

    def advance(self, ms: int) -> None:
        self._now += ms / 1000.0


class _SpySignal:
    def disconnect(self, *_args: Any) -> None:
        return None


class _SpyWorker:
    """Running worker stand-in; ``wait(ms)`` records ``ms``, advances the clock, times out."""

    def __init__(self, clock: FakeClock, *, join_ok: bool = False) -> None:
        self._clock = clock
        self._join_ok = join_ok
        self.waits: list[int] = []
        self.cancels = 0
        self.parse_progress = _SpySignal()
        self.parse_completed = _SpySignal()
        self.parse_failed = _SpySignal()
        self.parse_cancelled = _SpySignal()
        self.operation_completed = _SpySignal()
        self.operation_failed = _SpySignal()
        self.operation_cancelled = _SpySignal()
        self.finished = _SpySignal()

    def isRunning(self) -> bool:  # noqa: N802 - mirrors QThread API
        return True

    def cancel(self) -> None:
        self.cancels += 1

    def requestInterruption(self) -> None:  # noqa: N802 - mirrors QThread API
        return None

    def deleteLater(self) -> None:  # noqa: N802 - mirrors QThread API
        return None

    def wait(self, ms: int) -> bool:
        self.waits.append(ms)
        self._clock.advance(ms)
        return self._join_ok


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


def test_injected_policy_drives_default_teardown_waits(qapp) -> None:
    """``teardown()`` with no budget uses the policy budget and final join."""
    clock = FakeClock()
    policy = CollectionImportLifecyclePolicy(teardown_budget_ms=200, final_join_ms=30)
    actions = _make_actions(QWidget(), lifecycle_policy=policy, clock=clock)
    file_spy, library_spy = _SpyWorker(clock), _SpyWorker(clock)
    actions._worker = file_spy  # type: ignore[assignment]
    actions._library_worker = library_spy  # type: ignore[assignment]

    assert actions.teardown() is False
    assert file_spy.waits == [30]
    assert library_spy.waits == [30]
    assert library_spy.cancels >= 1


def test_deadline_passing_in_wait_idle_leaves_only_zero_probes(qapp, caplog) -> None:
    """P1 that exhausts the budget returns unclean; P2 and P3 only probe with wait(0)."""
    clock = FakeClock()
    actions = _make_actions(QWidget(), clock=clock)
    file_spy, library_spy = _SpyWorker(clock), _SpyWorker(clock)
    actions._worker = file_spy  # type: ignore[assignment]
    actions._library_worker = library_spy  # type: ignore[assignment]
    actions._state = CollectionImportState.PARSING
    clock.tick_ms = 60  # every deadline check moves time: 100 ms budget runs out in P1

    with caplog.at_level(logging.INFO, logger=_MODULE):
        clean = actions.teardown(timeout_ms=100)

    assert clean is False
    assert file_spy.waits == [0]
    assert library_spy.waits == [0]
    assert any(
        "collection_import_wait_idle_timeout" in r.message for r in caplog.records
    )


def test_wait_idle_without_app_polls_in_bounded_slices(qapp) -> None:
    """No QApplication: the poll slice is ``idle_poll_ms`` capped by what is left."""
    clock = FakeClock()
    actions = _make_actions(QWidget(), clock=clock)
    file_spy = _SpyWorker(clock)
    actions._worker = file_spy  # type: ignore[assignment]
    actions._state = CollectionImportState.PARSING

    with patch(f"{_MODULE}.QApplication.instance", return_value=None):
        assert actions.wait_idle(timeout_ms=25) is False

    assert file_spy.waits == [10, 10, 5]


def test_idle_teardown_is_clean_and_idempotent(qapp, caplog) -> None:
    actions = _make_actions(QWidget())
    with caplog.at_level(logging.DEBUG, logger=_MODULE):
        assert actions.teardown() is True
        assert actions.teardown() is True
    messages = [r.message for r in caplog.records]
    assert not any("collection_import_worker_interrupting" in m for m in messages)
    assert sum("teardown_completed clean=True" in m for m in messages) == 2


def test_presenter_teardown_defaults_to_policy_budget(qapp, caplog) -> None:
    """Presenter has no own default: ``None`` resolves to the policy budget (no 5 s wait)."""
    presenter = CollectionsPresenter(
        FakeRequestManager([]), FakeStateManager(), FakeMetrics(), {}
    )
    with caplog.at_level(logging.INFO):
        result = presenter.teardown()
    assert result.outcome == "success"
    messages = [r.message for r in caplog.records]
    assert "collections_presenter_teardown_started timeout_ms=5000" in messages
    assert "collection_import_teardown_started timeout_ms=5000" in messages


def test_teardown_timeout_logs_report_phase_waits_and_elapsed(qapp, caplog) -> None:
    """Join timeouts log the wait each phase got and the deadline elapsed (PYPOST-1264 S6)."""
    clock = FakeClock()
    policy = CollectionImportLifecyclePolicy(teardown_budget_ms=200, final_join_ms=30)
    actions = _make_actions(QWidget(), lifecycle_policy=policy, clock=clock)
    actions._worker = _SpyWorker(clock)  # type: ignore[assignment]
    actions._library_worker = _SpyWorker(clock)  # type: ignore[assignment]

    with caplog.at_level(logging.INFO, logger=_MODULE):
        assert actions.teardown() is False

    messages = [r.message for r in caplog.records]
    assert "collection_import_teardown_started timeout_ms=200" in messages
    assert "collection_library_import_worker_cancelling phase=p0" in messages
    assert "collection_library_import_worker_cancelling phase=p3" in messages
    assert (
        "collection_import_worker_interrupt_timeout wait_ms=30 elapsed_ms=30" in messages
    )
    assert (
        "collection_library_import_worker_timeout wait_ms=30 elapsed_ms=60" in messages
    )
    assert (
        "collection_import_teardown_completed clean=False elapsed_ms=60 timeout_ms=200"
        in messages
    )
    levels = {
        r.message.split(" ", 1)[0]: r.levelno
        for r in caplog.records
        if "_timeout" in r.message or "_cancelling" in r.message
    }
    assert levels == {
        "collection_import_worker_interrupt_timeout": logging.WARNING,
        "collection_library_import_worker_timeout": logging.WARNING,
        "collection_library_import_worker_cancelling": logging.WARNING,
    }


def test_library_join_success_logs_bounded_wait(qapp, caplog) -> None:
    """Honored library cancel logs the final-join bound that was granted (PYPOST-1324 S6)."""
    clock = FakeClock()
    policy = CollectionImportLifecyclePolicy(teardown_budget_ms=200, final_join_ms=30)
    actions = _make_actions(QWidget(), lifecycle_policy=policy, clock=clock)
    actions._library_worker = _SpyWorker(clock, join_ok=True)  # type: ignore[assignment]

    with caplog.at_level(logging.INFO, logger=_MODULE):
        assert actions.teardown() is True

    messages = [r.message for r in caplog.records]
    assert "collection_library_import_worker_cancelling phase=p0" in messages
    assert "collection_library_import_worker_cancelling phase=p3" in messages
    assert (
        "collection_library_import_worker_cancelled wait_ms=30 elapsed_ms=30" in messages
    )
    assert (
        "collection_import_teardown_completed clean=True elapsed_ms=30 timeout_ms=200"
        in messages
    )


def test_library_operation_cancelled_tracks_cancelled_outcome(qapp, caplog) -> None:
    """Cooperative library stop uses outcome=cancelled, not rejected (PYPOST-1324 S6)."""
    metrics = MagicMock()
    registry = MetricsRegistry()
    actions = _make_actions(QWidget(), metrics=metrics)
    actions._state = CollectionImportState.PREPARING

    with caplog.at_level(logging.INFO, logger=_MODULE):
        actions._on_library_operation_cancelled()

    assert actions._state is CollectionImportState.IDLE
    metrics.track_gui_library_operation.assert_called_once_with(
        "collection_import_library", "cancelled"
    )
    registry.track_gui_library_operation("collection_import_library", "cancelled")
    assert (
        registry.gui_library_operations.labels(
            operation="collection_import_library", outcome="cancelled"
        )._value.get()
        == 1.0
    )
    assert any(
        r.message == "collection_library_import_operation_cancelled from_state=preparing"
        for r in caplog.records
    )


def test_exhausted_budget_logs_zero_wait_probes(qapp, caplog) -> None:
    """When P1 used the whole budget, later timeouts log ``wait_ms=0`` (no time left)."""
    clock = FakeClock()
    actions = _make_actions(QWidget(), clock=clock)
    actions._worker = _SpyWorker(clock)  # type: ignore[assignment]
    actions._library_worker = _SpyWorker(clock)  # type: ignore[assignment]
    actions._state = CollectionImportState.PARSING
    clock.tick_ms = 60

    with caplog.at_level(logging.INFO, logger=_MODULE):
        assert actions.teardown(timeout_ms=100) is False

    messages = [r.message for r in caplog.records]
    assert any(
        m.startswith("collection_import_worker_interrupt_timeout wait_ms=0 elapsed_ms=")
        for m in messages
    )
    assert any(
        m.startswith("collection_library_import_worker_timeout wait_ms=0 elapsed_ms=")
        for m in messages
    )
    completed = [m for m in messages if m.startswith("collection_import_teardown_completed")]
    assert len(completed) == 1
    assert completed[0].startswith("collection_import_teardown_completed clean=False ")
    assert completed[0].endswith(" timeout_ms=100")


def test_nested_worker_finish_join_overrun_during_wait_idle(qapp, caplog) -> None:
    """Risk 3: nested finish join during P1 is uncapped and warns on stall.

    Characterization of PYPOST-1264 design Risk 3 (PYPOST-1322). When
    ``_on_worker_finished`` runs inside wait-idle ``processEvents`` after the
    remaining caller budget is exhausted, the join still waits the full
    ``worker_finish_join_ms`` (not deadline-bounded), teardown overrun past the
    caller budget attributable to that join is at most that allowance, and the
    stall path emits ``collection_import_worker_finish_wait_timeout``.
    """
    join_ms = 100
    budget_ms = 50
    clock = FakeClock()
    policy = CollectionImportLifecyclePolicy(
        teardown_budget_ms=200,
        final_join_ms=30,
        worker_finish_join_ms=join_ms,
    )
    actions = _make_actions(QWidget(), lifecycle_policy=policy, clock=clock)
    file_spy = _SpyWorker(clock, join_ok=False)
    actions._worker = file_spy  # type: ignore[assignment]
    actions._state = CollectionImportState.PARSING
    t0 = clock._now
    nest_fired = False

    def nested_process_events(*_args: Any, **_kwargs: Any) -> None:
        nonlocal nest_fired
        if nest_fired:
            return
        nest_fired = True
        # Exhaust remaining caller budget, then nest the finish join (Risk 3).
        clock.advance(budget_ms)
        actions._on_worker_finished()
        actions._state = CollectionImportState.IDLE

    with (
        caplog.at_level(logging.WARNING, logger=_MODULE),
        patch.object(qapp, "processEvents", side_effect=nested_process_events),
    ):
        actions.teardown(timeout_ms=budget_ms)

    assert file_spy.waits == [join_ms]
    elapsed_ms = int(round((clock._now - t0) * 1000))
    overrun_ms = max(0, elapsed_ms - budget_ms)
    assert overrun_ms <= join_ms
    assert any(
        r.levelno == logging.WARNING
        and f"collection_import_worker_finish_wait_timeout wait_ms={join_ms}"
        in r.message
        for r in caplog.records
    )
