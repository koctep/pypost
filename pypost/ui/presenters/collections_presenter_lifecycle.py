"""Lifecycle coordination helpers for the collections presenter."""

from __future__ import annotations

import logging
import threading
import time
from typing import TYPE_CHECKING

from pypost.core.collection_import_state import CollectionImportState
from pypost.core.lifecycle import (
    TeardownResult,
    record_teardown_metrics,
    teardown_correlation_id,
)

if TYPE_CHECKING:
    from pypost.ui.presenters.collections_presenter import CollectionsPresenter

logger = logging.getLogger(__name__)


def ensure_lifecycle_state(presenter: CollectionsPresenter) -> None:
    """Install teardown fencing fields if the presenter was constructed without them."""
    if getattr(presenter, "_teardown_lock", None) is None:
        setattr(presenter, "_teardown_lock", threading.Lock())
    if not hasattr(presenter, "_teardown_started"):
        setattr(presenter, "_teardown_started", False)
    if not hasattr(presenter, "_teardown_result"):
        setattr(presenter, "_teardown_result", None)


def _fence_admission(presenter: CollectionsPresenter) -> None:
    """Reject new import/create admission; no-op once a TeardownResult exists."""
    if getattr(presenter, "_teardown_result", None) is not None:
        return
    setattr(presenter, "_teardown_started", True)
    presenter._collection_creation_closed = True
    presenter._import_actions.begin_teardown()


def begin_teardown(presenter: CollectionsPresenter) -> None:
    """Fence import admission without waiting or closing the panel."""
    ensure_lifecycle_state(presenter)
    with getattr(presenter, "_teardown_lock"):
        _fence_admission(presenter)


def teardown(
    presenter: CollectionsPresenter, timeout_ms: int | None = None
) -> TeardownResult:
    """Fence admission, tear down import work, and close the collections panel."""
    ensure_lifecycle_state(presenter)
    with getattr(presenter, "_teardown_lock"):
        existing = getattr(presenter, "_teardown_result", None)
        if isinstance(existing, TeardownResult):
            return existing
        started = time.monotonic()
        correlation_id = teardown_correlation_id(presenter)
        _fence_admission(presenter)

        actions = presenter._import_actions
        active_count = 0
        worker = getattr(actions, "_worker", None)
        if worker is not None and worker.isRunning():
            active_count += 1
        library_worker = getattr(actions, "_library_worker", None)
        if library_worker is not None and library_worker.isRunning():
            active_count += 1
        state = getattr(actions, "_state", CollectionImportState.IDLE)
        pending_count = 0 if state is CollectionImportState.IDLE else 1

        budget_ms = actions.lifecycle_policy.resolve_budget_ms(timeout_ms)
        logger.info(
            "lifecycle_teardown_started owner=collections_presenter teardown_id=%s "
            "timeout_ms=%d active_count=%d pending_count=%d",
            correlation_id,
            budget_ms,
            active_count,
            pending_count,
        )
        # Keep the existing presenter diagnostic line for PYPOST-1264 callers.
        logger.info("collections_presenter_teardown_started timeout_ms=%d", budget_ms)

        clean = actions.teardown(timeout_ms=timeout_ms)
        presenter._panel.close()
        logger.info("collections_presenter_teardown_completed clean=%s", clean)

        outcome = "success" if clean else "incomplete"
        result = TeardownResult(
            owner="collections_presenter",
            outcome=outcome,
            elapsed_ms=int((time.monotonic() - started) * 1000),
            active_count=active_count,
            pending_count=pending_count,
            failure_kind=None if clean else "timeout",
        )
        setattr(presenter, "_teardown_result", result)
        logger.info(
            "lifecycle_teardown_completed owner=collections_presenter teardown_id=%s "
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
