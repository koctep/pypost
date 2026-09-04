"""Lifecycle coordination helpers for request tabs."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import TYPE_CHECKING

from pypost.core.lifecycle import (
    TeardownResult,
    record_environment_update_disposition,
    record_lifecycle_event,
    record_teardown_metrics,
    teardown_correlation_id,
)

if TYPE_CHECKING:
    from pypost.core.qt.worker import RequestWorker
    from pypost.ui.presenters.tabs_presenter import RequestTab, TabsPresenter


logger = logging.getLogger(__name__)


def begin_teardown(presenter: TabsPresenter) -> None:
    """Atomically close request and environment-update admission."""
    with presenter._teardown_lock:
        if presenter._teardown_result is None:
            presenter._teardown_started = True


def teardown_tab(
    presenter: TabsPresenter,
    tab: RequestTab,
    timeout_ms: int | None = None,
) -> TeardownResult:
    """Fence and boundedly stop one request tab without closing the workspace."""
    budget_ms = 5000 if timeout_ms is None else max(0, timeout_ms)
    tab_key = id(tab)
    with presenter._teardown_lock:
        if tab_key in presenter._tab_teardown_results:
            return presenter._tab_teardown_results[tab_key]
        started = time.monotonic()
        presenter._fenced_tabs.add(tab_key)
        tab._request_generation += 1
        tab._terminal_claimed = True
        worker = tab.worker
        active_count = int(worker is not None and worker.isRunning())
        correlation_id = teardown_correlation_id(presenter)
        logger.info(
            "lifecycle_teardown_started owner=request_tab teardown_id=%s "
            "timeout_ms=%d active_count=%d pending_count=0",
            correlation_id,
            budget_ms,
            active_count,
        )
        if worker is not None and worker.isRunning():
            worker.stop()
        presenter._discard_chunk_buffer(tab)
        settled = worker is None or not worker.isRunning() or _wait_for_worker(worker, budget_ms)
        if settled and tab.worker is worker:
            tab.worker = None
        result = TeardownResult(
            owner="request_tab",
            outcome="success" if settled else "incomplete",
            elapsed_ms=int((time.monotonic() - started) * 1000),
            active_count=active_count,
            failure_kind=None if settled else "timeout",
        )
        presenter._tab_teardown_results[tab_key] = result
        logger.info(
            "lifecycle_teardown_completed owner=request_tab teardown_id=%s "
            "outcome=%s elapsed_ms=%d active_count=%d pending_count=0",
            correlation_id,
            result.outcome,
            result.elapsed_ms,
            result.active_count,
        )
        record_teardown_metrics(presenter, result, presenter._metrics)
        return result


def teardown(presenter: TabsPresenter, timeout_ms: int | None = None) -> TeardownResult:
    """Fence request delivery, drain accepted updates, and stop workers."""
    budget_ms = 5000 if timeout_ms is None else max(0, timeout_ms)
    with presenter._teardown_lock:
        if presenter._teardown_result is not None:
            return presenter._teardown_result
        started = time.monotonic()
        correlation_id = teardown_correlation_id(presenter)
        presenter._teardown_started = True
        cutoff = presenter._env_update_ledger.cutoff()
        presenter._env_update_cutoff = cutoff
        from pypost.ui.presenters.tabs_presenter import RequestTab

        request_tabs: list[RequestTab] = []
        for index in range(presenter._tabs.count()):
            tab = presenter._tabs.widget(index)
            if isinstance(tab, RequestTab):
                request_tabs.append(tab)
        workers = [tab.worker for tab in request_tabs if tab.worker is not None]
        active_count = sum(int(worker.isRunning()) for worker in workers)
        pending_count = len(presenter._chunk_buffers) + len(
            presenter._env_update_ledger.pending(cutoff)
        )
        logger.info(
            "lifecycle_teardown_started owner=tabs_presenter teardown_id=%s "
            "timeout_ms=%d active_count=%d pending_count=%d",
            correlation_id,
            budget_ms,
            active_count,
            pending_count,
        )
        for tab in request_tabs:
            presenter._fenced_tabs.add(id(tab))
            tab._request_generation += 1
            tab._terminal_claimed = True
            presenter._discard_chunk_buffer(tab)
        for worker in workers:
            if worker.isRunning():
                worker.stop()
        if active_count:
            record_lifecycle_event(
                presenter, "cancellation_requested", active_count, presenter._metrics
            )
        deadline = started + budget_ms / 1000
        settled = True
        for tab in request_tabs:
            tab_worker = tab.worker
            if tab_worker is None or not tab_worker.isRunning():
                continue
            remaining_ms = max(0, int((deadline - time.monotonic()) * 1000))
            if not _wait_for_worker(tab_worker, remaining_ms):
                settled = False
            elif tab.worker is tab_worker:
                tab.worker = None

        drain = getattr(presenter, "_env_update_consumer", None)
        handed_off = drain is not None
        if drain is not None:
            settled = _drain_updates(presenter, drain, cutoff) and settled
        pending = presenter._env_update_ledger.pending(cutoff)
        if pending and not handed_off:
            for record in pending:
                presenter._env_update_ledger.mark(record.sequence, "incomplete")
            settled = False
        result = TeardownResult(
            owner="tabs_presenter",
            outcome="success" if settled else "incomplete",
            elapsed_ms=int((time.monotonic() - started) * 1000),
            active_count=active_count,
            pending_count=pending_count,
            failure_kind=None if settled else "timeout",
            dispositions=presenter._env_update_ledger.dispositions_view(),
        )
        presenter._teardown_result = result
        logger.info(
            "lifecycle_teardown_completed owner=tabs_presenter teardown_id=%s "
            "outcome=%s elapsed_ms=%d deadline_ms=%d active_count=%d pending_count=%d",
            correlation_id,
            result.outcome,
            result.elapsed_ms,
            budget_ms,
            result.active_count,
            result.pending_count,
        )
        record_teardown_metrics(presenter, result, presenter._metrics)
        return result


def set_environment_update_consumer(
    presenter: TabsPresenter,
    consumer: Callable[[dict[str, str], int], None],
) -> None:
    presenter._env_update_consumer = consumer


def drain_accepted_env_updates(
    presenter: TabsPresenter,
    consumer: Callable[[dict[str, str], int], None],
    cutoff: int | None = None,
) -> bool:
    """Deliver accepted payloads through the durable consumer seam."""
    return _drain_updates(presenter, consumer, cutoff)


def _drain_updates(
    presenter: TabsPresenter,
    consumer: Callable[[dict[str, str], int], None],
    cutoff: int | None,
) -> bool:
    all_delivered = True
    for record in presenter._env_update_ledger.pending(cutoff):
        try:
            consumer(record.variables, record.sequence)
        except Exception:
            presenter._env_update_ledger.mark(record.sequence, "failed")
            all_delivered = False
    return all_delivered


def record_env_update_disposition(
    presenter: TabsPresenter,
    sequence: int,
    disposition: str,
) -> None:
    presenter._env_update_ledger.mark(sequence, disposition)
    record_environment_update_disposition(disposition, presenter._metrics)


def _wait_for_worker(worker: RequestWorker, timeout_ms: int) -> bool:
    """Bound a worker join while allowing cooperative fakes and Qt workers to settle."""
    deadline = time.monotonic() + max(0, timeout_ms) / 1000
    while worker.isRunning():
        remaining_ms = max(0, int((deadline - time.monotonic()) * 1000))
        if not worker.wait(min(remaining_ms, 10)) and remaining_ms == 0:
            return False
        if worker.isRunning() and time.monotonic() < deadline:
            time.sleep(0.001)
    return True
