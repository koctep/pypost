from __future__ import annotations

import json
import logging
import threading
import time
from pathlib import Path
from typing import Callable, List

from platformdirs import user_data_dir

from pypost.models.models import HistoryEntry

logger = logging.getLogger(__name__)


class HistoryManager:
    DEFAULT_MAX_ENTRIES: int = 500

    def __init__(
        self,
        app_name: str = "pypost",
        max_entries: int = DEFAULT_MAX_ENTRIES,
        history_path: Path | None = None,
        *,
        defer_initial_load: bool = False,
    ) -> None:
        self._max_entries = max_entries
        self._lock = threading.Lock()
        self._load_state_lock = threading.Lock()
        self._save_lock = threading.Lock()
        self._save_running = False
        self._save_pending = False
        self._save_thread: threading.Thread | None = None
        self._load_thread: threading.Thread | None = None
        self._loaded = False
        self._entries: List[HistoryEntry] = []
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
        with self._load_state_lock:
            if self._loaded or self._load_thread is not None:
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

    def get_entries(self) -> List[HistoryEntry]:
        """Return a copy of all entries ordered newest-first (immutable snapshot)."""
        with self._lock:
            return list(self._entries)

    # ── Write ─────────────────────────────────────────────────────────────────

    def append(self, entry: HistoryEntry) -> None:
        """Thread-safe. Insert entry at front. Drops oldest when cap exceeded. Async save."""
        self._ensure_loaded()
        with self._lock:
            self._entries.insert(0, entry)
            cap_enforced = len(self._entries) > self._max_entries
            if cap_enforced:
                self._entries = self._entries[: self._max_entries]
            count = len(self._entries)
        logger.debug(
            "history_entry_appended method=%s url=%s count=%d", entry.method, entry.url, count
        )
        if cap_enforced:
            logger.warning(
                "history_cap_enforced max=%d oldest_entry_dropped=True", self._max_entries
            )
        self._save_async()

    def delete_entry(self, entry_id: str) -> None:
        """Remove the entry with the given id. Triggers an async save."""
        self._ensure_loaded()
        with self._lock:
            self._entries = [e for e in self._entries if e.id != entry_id]
            count = len(self._entries)
        logger.debug("history_entry_deleted entry_id=%s remaining=%d", entry_id, count)
        self._save_async()

    def clear(self) -> None:
        """Remove all entries. Triggers an async save."""
        self._ensure_loaded()
        with self._lock:
            count = len(self._entries)
            self._entries = []
        logger.debug("history_cleared count=%d", count)
        self._save_async()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _run_async_load(self, on_complete: Callable[[], None] | None) -> None:
        try:
            self._load()
        finally:
            with self._load_state_lock:
                self._loaded = True
            count = len(self._entries)
            logger.info("history_load_async_completed count=%d", count)
            if on_complete is not None:
                on_complete()

    def _wait_for_pending_load(self) -> None:
        with self._load_state_lock:
            thread = self._load_thread
        if thread is not None and thread.is_alive():
            thread.join()

    def _ensure_loaded(self) -> None:
        """Wait for async load and run a sync load when deferred startup never dispatched one."""
        self._wait_for_pending_load()
        with self._load_state_lock:
            if self._loaded:
                return
        self._load()
        with self._load_state_lock:
            self._loaded = True

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
            logger.warning("history_manager_load_failed path=%s error=%s", self._history_path, exc)
            self._entries = []

    def _save_async(self) -> None:
        """Serialize self._entries to JSON in a daemon thread (non-blocking, debounced)."""
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
                    logger.error(
                        "history_manager_save_failed elapsed_ms=%.1f error=%s",
                        (time.monotonic() - _t0) * 1000,
                        exc,
                    )
                with self._save_lock:
                    if not self._save_pending:
                        self._save_running = False
                        return
                    self._save_pending = False

        self._save_thread = t = threading.Thread(target=_run, daemon=True)
        t.start()

    def flush(self) -> None:
        """Block until any in-progress async save has completed.

        Safe to call even if no save has been triggered. Intended for tests
        and teardown code that must synchronize before the storage path is
        cleaned up.
        """
        with self._save_lock:
            thread = self._save_thread
        if thread is not None:
            logger.debug("history_manager_flush waiting thread_id=%s", thread.ident)
            thread.join()
            logger.debug("history_manager_flush complete")
