from __future__ import annotations

import json
import logging
import threading
import time
from collections.abc import Callable
from pathlib import Path

from platformdirs import user_data_dir

from pypost.core.lifecycle import (
    TeardownResult,
    record_history_io_failure,
    record_lifecycle_event,
    record_teardown_metrics,
    teardown_correlation_id,
)
from pypost.core.metrics_protocol import MetricsTrackerProtocol, resolve_metrics
from pypost.models.models import HistoryEntry

logger = logging.getLogger(__name__)


class HistoryManager:
    DEFAULT_MAX_ENTRIES: int = 500
    DEFAULT_LIFECYCLE_TIMEOUT_MS: int = 5000

    def __init__(
        self,
        app_name: str = "pypost",
        max_entries: int = DEFAULT_MAX_ENTRIES,
        history_path: Path | None = None,
        *,
        defer_initial_load: bool = False,
        metrics: MetricsTrackerProtocol | None = None,
    ) -> None:
        self._max_entries = max_entries
        self._metrics = resolve_metrics(metrics)
        self._lifecycle_metric_owner = "history_manager"
        self._lock = threading.Lock()
        self._load_state_lock = threading.Lock()
        self._save_lock = threading.Lock()
        self._save_running = False
        self._save_pending = False
        self._save_thread: threading.Thread | None = None
        self._load_thread: threading.Thread | None = None
        self._loaded = False
        self._entries: list[HistoryEntry] = []
        # Writes accepted while the initial load is still in flight are kept
        # as ordered operations.  They must be replayed after the load rather
        # than applied to a snapshot that the load can overwrite.
        self._pending_writes: list[tuple[str, object]] = []
        # Admission and save registration share this boundary.  In
        # particular, teardown must not observe the gap between a write being
        # accepted and its save thread being registered.
        self._lifecycle_lock = threading.RLock()
        self._write_condition = threading.Condition(self._lifecycle_lock)
        self._active_writes = 0
        self._teardown_lock = threading.Lock()
        self._teardown_started = False
        self._teardown_result: TeardownResult | None = None
        self._last_save_failure: BaseException | None = None
        if history_path is not None:
            self._history_path = Path(history_path)
        else:
            self._history_path = Path(user_data_dir(app_name)) / "history.json"
        if not defer_initial_load:
            self._load()
            self._loaded = True

    @property
    def is_loaded(self) -> bool:
        with self._load_state_lock:
            return self._loaded

    def load_async(self, on_complete: Callable[[], None] | None = None) -> bool:
        """Load history.json in a daemon thread. Returns False when load already done or running."""
        with self._lifecycle_lock:
            with self._load_state_lock:
                if self._teardown_started or self._loaded or self._load_thread is not None:
                    if self._teardown_started:
                        record_lifecycle_event(
                            self, "admission_rejected", metrics=self._metrics
                        )
                    return False
                thread = threading.Thread(
                    target=self._run_async_load,
                    args=(on_complete,),
                    daemon=True,
                )
                self._load_thread = thread
                thread.start()
        logger.info("history_load_async_dispatched path=%s", self._history_path)
        return True

    # ── Read ──────────────────────────────────────────────────────────────────

    def get_entries(self) -> list[HistoryEntry]:
        """Return a copy of all entries ordered newest-first (immutable snapshot)."""
        with self._lock:
            return list(self._entries)

    # ── Write ─────────────────────────────────────────────────────────────────

    def append(self, entry: HistoryEntry) -> None:
        """Thread-safe. Insert entry at front. Drops oldest when cap exceeded. Async save."""
        if not self._admit_write():
            return
        try:
            if not self._ensure_loaded(self.DEFAULT_LIFECYCLE_TIMEOUT_MS):
                self._queue_or_apply_write("append", entry)
                logger.warning("history_write_deferred reason=load_timeout owner=history_manager")
                return
            with self._lock:
                self._entries.insert(0, entry)
                cap_enforced = len(self._entries) > self._max_entries
                if cap_enforced:
                    self._entries = self._entries[: self._max_entries]
                count = len(self._entries)
            self._save_async(accepted_during_teardown=True)
        finally:
            self._release_write()
        logger.debug(
            "history_entry_appended method=%s url=%s count=%d", entry.method, entry.url, count
        )
        if cap_enforced:
            logger.warning(
                "history_cap_enforced max=%d oldest_entry_dropped=True", self._max_entries
            )

    def delete_entry(self, entry_id: str) -> None:
        """Remove the entry with the given id. Triggers an async save."""
        if not self._admit_write():
            return
        try:
            if not self._ensure_loaded(self.DEFAULT_LIFECYCLE_TIMEOUT_MS):
                self._queue_or_apply_write("delete", entry_id)
                logger.warning("history_write_deferred reason=load_timeout owner=history_manager")
                return
            with self._lock:
                self._entries = [e for e in self._entries if e.id != entry_id]
                count = len(self._entries)
            self._save_async(accepted_during_teardown=True)
        finally:
            self._release_write()
        logger.debug("history_entry_deleted entry_id=%s remaining=%d", entry_id, count)

    def clear(self) -> None:
        """Remove all entries. Triggers an async save."""
        if not self._admit_write():
            return
        try:
            if not self._ensure_loaded(self.DEFAULT_LIFECYCLE_TIMEOUT_MS):
                self._queue_or_apply_write("clear", None)
                logger.warning("history_write_deferred reason=load_timeout owner=history_manager")
                return
            with self._lock:
                count = len(self._entries)
                self._entries = []
            self._save_async(accepted_during_teardown=True)
        finally:
            self._release_write()
        logger.debug("history_cleared count=%d", count)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _run_async_load(self, on_complete: Callable[[], None] | None) -> None:
        try:
            self._load()
        finally:
            with self._load_state_lock:
                self._loaded = True
            self._apply_pending_writes_if_loaded()
            count = len(self._entries)
            logger.info("history_load_async_completed count=%d", count)
            if on_complete is not None:
                on_complete()

    def _wait_for_pending_load(self, timeout_ms: int | None = None) -> bool:
        with self._load_state_lock:
            thread = self._load_thread
        if thread is not None and thread.is_alive():
            thread.join(
                None if timeout_ms is None else max(0, timeout_ms) / 1000
            )
            settled = not thread.is_alive()
            if settled:
                self._apply_pending_writes_if_loaded()
            return settled
        self._apply_pending_writes_if_loaded()
        return True

    def _ensure_loaded(self, timeout_ms: int | None = None) -> bool:
        """Wait for async load and run a sync load when deferred startup never dispatched one."""
        if not self._wait_for_pending_load(timeout_ms):
            return False
        with self._load_state_lock:
            if self._loaded:
                return True
        self._load()
        with self._load_state_lock:
            self._loaded = True
        self._apply_pending_writes_if_loaded()
        return True

    def _queue_or_apply_write(self, operation: str, value: object) -> None:
        """Retain an accepted write until a deferred load has a stable snapshot."""
        with self._lifecycle_lock:
            with self._load_state_lock:
                loaded = self._loaded
            if not loaded:
                self._pending_writes.append((operation, value))
                return
            changed = self._apply_write_locked(operation, value)
        if changed:
            self._save_async(accepted_during_teardown=True)

    def _apply_pending_writes_if_loaded(self) -> None:
        with self._lifecycle_lock:
            with self._load_state_lock:
                if not self._loaded or not self._pending_writes:
                    return
            pending = self._pending_writes
            self._pending_writes = []
            for operation, value in pending:
                self._apply_write_locked(operation, value)
        self._save_async(accepted_during_teardown=True)

    def _apply_write_locked(self, operation: str, value: object) -> bool:
        with self._lock:
            if operation == "append":
                self._entries.insert(0, value)  # type: ignore[arg-type]
                self._entries = self._entries[: self._max_entries]
            elif operation == "delete":
                self._entries = [entry for entry in self._entries if entry.id != value]
            elif operation == "clear":
                self._entries = []
            else:  # pragma: no cover - only internal operation names are used
                return False
        return True

    def _admit_write(self) -> bool:
        with self._lifecycle_lock:
            if self._teardown_started:
                logger.warning("history_write_rejected reason=teardown owner=history_manager")
                record_lifecycle_event(
                    self, "admission_rejected", metrics=self._metrics
                )
                return False
            self._active_writes += 1
            return True

    def _release_write(self) -> None:
        with self._write_condition:
            self._active_writes -= 1
            self._write_condition.notify_all()

    def _load(self) -> None:
        """Read history.json; populate self._entries. Handles all I/O errors."""
        if not self._history_path.exists():
            logger.debug("history_manager_no_file path=%s", self._history_path)
            return
        try:
            with open(self._history_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            entries = [HistoryEntry(**item) for item in data]
            with self._lock:
                self._entries = entries
            logger.debug("history_manager_loaded count=%d", len(self._entries))
        except Exception as exc:
            record_history_io_failure("load", self._metrics)
            logger.warning("history_manager_load_failed path=%s error=%s", self._history_path, exc)
            self._entries = []

    def _save_async(self, *, accepted_during_teardown: bool = False) -> None:
        """Serialize self._entries to JSON in a daemon thread (non-blocking, debounced)."""
        with self._lifecycle_lock:
            if self._teardown_started and not accepted_during_teardown:
                return
            with self._save_lock:
                self._save_pending = True
                if self._save_running:
                    return
                self._save_running = True

        def _run() -> None:
            while True:
                with self._lock:
                    snapshot = list(self._entries)
                _t0 = time.monotonic()
                try:
                    self._history_path.parent.mkdir(parents=True, exist_ok=True)
                    data = [e.model_dump() for e in snapshot]
                    with open(self._history_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                    logger.debug(
                        "history_manager_saved count=%d elapsed_ms=%.1f",
                        len(snapshot),
                        (time.monotonic() - _t0) * 1000,
                    )
                except Exception as exc:
                    with self._save_lock:
                        self._last_save_failure = exc
                    record_history_io_failure("save", self._metrics)
                    logger.error(
                        "history_manager_save_failed elapsed_ms=%.1f error=%s",
                        (time.monotonic() - _t0) * 1000,
                        exc,
                    )
                else:
                    with self._save_lock:
                        self._last_save_failure = None
                with self._save_lock:
                    if not self._save_pending:
                        self._save_running = False
                        return
                    self._save_pending = False

        with self._save_lock:
            self._save_thread = t = threading.Thread(target=_run, daemon=True)
            t.start()

    def flush(self, timeout_ms: int | None = None) -> bool:
        """Block until any in-progress async save has completed.

        Safe to call even if no save has been triggered. Intended for tests
        and teardown code that must synchronize before the storage path is
        cleaned up. ``timeout_ms`` bounds the wait when supplied.
        """
        with self._save_lock:
            thread = self._save_thread
        if thread is not None:
            logger.debug("history_manager_flush waiting thread_id=%s", thread.ident)
            thread.join(None if timeout_ms is None else max(0, timeout_ms) / 1000)
            logger.debug("history_manager_flush complete")
            return not thread.is_alive()
        return True

    def begin_teardown(self) -> None:
        """Close history admission before the composition root drains writes."""
        with self._lifecycle_lock:
            if self._teardown_result is None:
                self._teardown_started = True

    def teardown(self, timeout_ms: int | None = None) -> TeardownResult:
        """Fence new work and drain accepted history I/O within one deadline."""
        budget_ms = 5000 if timeout_ms is None else max(0, timeout_ms)
        with self._teardown_lock:
            if self._teardown_result is not None:
                return self._teardown_result
            started = time.monotonic()
            correlation_id = teardown_correlation_id(self)
            with self._lifecycle_lock:
                self._teardown_started = True
                with self._load_state_lock:
                    load_thread = self._load_thread
                with self._save_lock:
                    save_thread = self._save_thread
                    pending = self._save_pending
                active_writes = self._active_writes
                pending_writes = len(self._pending_writes)
            active_count = int(load_thread is not None and load_thread.is_alive())
            active_count += int(save_thread is not None and save_thread.is_alive())
            pending_count = int(bool(pending)) + pending_writes
            logger.info(
                "lifecycle_teardown_started owner=history_manager teardown_id=%s "
                "timeout_ms=%d active_count=%d pending_count=%d",
                correlation_id,
                budget_ms,
                active_count,
                pending_count,
            )

            deadline = started + budget_ms / 1000
            with self._write_condition:
                while self._active_writes and time.monotonic() < deadline:
                    self._write_condition.wait(max(0.0, deadline - time.monotonic()))
                active_writes_settled = self._active_writes == 0
            load_settled = True
            if load_thread is not None and load_thread.is_alive():
                remaining = max(0.0, deadline - time.monotonic())
                load_thread.join(remaining)
                load_settled = not load_thread.is_alive()
            remaining_ms = max(0, int((deadline - time.monotonic()) * 1000))
            save_settled = self.flush(timeout_ms=remaining_ms)
            if not active_writes_settled or not load_settled or not save_settled:
                outcome = "incomplete"
                failure_kind = "timeout"
            elif self._last_save_failure is not None:
                outcome = "failed"
                failure_kind = "worker_error"
            else:
                outcome = "success"
                failure_kind = None
            result = TeardownResult(
                owner="history_manager",
                outcome=outcome,
                elapsed_ms=int((time.monotonic() - started) * 1000),
                active_count=active_count + active_writes,
                pending_count=pending_count,
                failure_kind=failure_kind,
            )
            self._teardown_result = result
            logger.info(
                "lifecycle_teardown_completed owner=history_manager teardown_id=%s "
                "outcome=%s elapsed_ms=%d deadline_ms=%d active_count=%d "
                "pending_count=%d",
                correlation_id,
                result.outcome,
                result.elapsed_ms,
                budget_ms,
                result.active_count,
                result.pending_count,
            )
            record_teardown_metrics(self, result, self._metrics)
            return result
