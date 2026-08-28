"""Import Collection orchestration for the collections sidebar (PYPOST-987).

Split out of ``CollectionsPresenter`` the same way ``CollectionTreeActions`` and
``CollectionsAsyncLoader`` are: the presenter owns the tree and the panel, this
owns the picker → async parse → prompt → plan → persist → refresh flow. Parse
runs on a ``QThread`` (PYPOST-1005); conflict prompts and apply stay on the GUI
thread. All decision logic lives in the Qt-free
``pypost.core.collection_import``; this module only sequences it against dialogs
and app state.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QElapsedTimer, QObject
from PySide6.QtWidgets import QApplication, QPushButton, QWidget

from pypost.core.collection_import import (
    CollectionImportFileError,
    find_collection_conflicts,
    format_collection_import_result,
    plan_collection_import,
    recount_collection_import_plan,
)
from pypost.core.collection_import_apply import apply_imported_collections
from pypost.core.collection_messages import (
    MSG_IMPORT_NO_VALID_COLLECTIONS,
    MSG_IMPORT_PREPARING,
    format_import_validating_message,
)
from pypost.core.import_conflicts import ImportConflictDecision
from pypost.core.qt.collection_import_parse_worker import (
    CollectionImportParseWorker,
    ReadImportFile,
)
from pypost.core.request_manager import RequestManager
from pypost.models.models import Collection
from pypost.ui.collection_item_dialogs import (
    prompt_collection_import_conflict,
    prompt_import_collection_file,
    show_collection_import_invalid_file_error,
    show_collection_import_result,
)
from pypost.ui.widget_ids import COLLECTION_IMPORT_BUTTON

logger = logging.getLogger(__name__)

# Short join after QThread.finished so native cleanup completes before GC/delete
# (PYPOST-829 H3). Bound must stay small — slot runs on the GUI thread.
_WORKER_FINISH_WAIT_MS = 100


class CollectionImportActions(QObject):
    """Runs one Import Collection interaction end to end."""

    def __init__(
        self,
        parent_widget: QWidget,
        request_manager: RequestManager,
        *,
        read_import_file: ReadImportFile,
        refresh_tree: Callable[[], None],
        restore_tree_state: Callable[[], None],
        emit_collections_changed: Callable[[], None],
        show_status: Callable[[str], None] | None = None,
        clear_status: Callable[[], None] | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._parent = parent_widget
        self._request_manager = request_manager
        self._read_import_file = read_import_file
        self._refresh_tree = refresh_tree
        self._restore_tree_state = restore_tree_state
        self._emit_collections_changed = emit_collections_changed
        self._show_status = show_status
        self._clear_status = clear_status
        self._worker: CollectionImportParseWorker | None = None
        self._preparing = False

    def is_busy(self) -> bool:
        """True while a parse worker is in flight (busy cue / re-entry guard)."""
        if self._preparing:
            return True
        return self._worker is not None and self._worker.isRunning()

    def wait_idle(self, timeout_ms: int = 5000) -> bool:
        """Pump event loop / wait until background worker has finished and joined."""
        if not self.is_busy():
            return True

        timer = QElapsedTimer()
        timer.start()
        app = QApplication.instance()
        logger.info("collection_import_wait_idle_started")
        while self.is_busy():
            if timer.elapsed() >= timeout_ms:
                logger.warning(
                    "collection_import_wait_idle_timeout elapsed_ms=%d",
                    timer.elapsed(),
                )
                return False
            if app is not None:
                app.processEvents()
            elif self._worker is not None:
                self._worker.wait(10)
        logger.info(
            "collection_import_wait_idle_completed elapsed_ms=%d",
            timer.elapsed(),
        )
        return True

    def import_collections(self) -> None:
        """Pick a file, parse off-thread, then finish import on the GUI thread."""
        if self.is_busy():
            logger.info("collection_import_skipped reason=busy")
            return

        path = prompt_import_collection_file(self._parent)
        if path is None:
            return

        self._start_parse(path)

    def _start_parse(self, path: Path) -> None:
        self._set_preparing(True)
        worker = CollectionImportParseWorker(path, self._read_import_file)
        worker.parse_progress.connect(self._on_parse_progress)
        worker.parse_completed.connect(self._on_parse_completed)
        worker.parse_failed.connect(self._on_parse_failed)
        worker.finished.connect(self._on_worker_finished)
        self._worker = worker
        worker.start()
        logger.info("collection_import_parse_started path=%s", path)

    def _on_parse_progress(self, done: int, total: int) -> None:
        if self._show_status is not None:
            self._show_status(format_import_validating_message(done, total))

    def _on_parse_completed(
        self,
        collections: list[Collection],
        parse_errors: list[str],
    ) -> None:
        self._set_preparing(False)
        if not collections:
            logger.warning("collection_import_file_invalid reason=no_valid_collections")
            message = MSG_IMPORT_NO_VALID_COLLECTIONS
            if parse_errors:
                message = "\n".join([message, ""] + parse_errors)
            show_collection_import_invalid_file_error(self._parent, message)
            return
        self._finish_import(collections, parse_errors)

    def _on_parse_failed(self, error: object) -> None:
        self._set_preparing(False)
        if isinstance(error, CollectionImportFileError):
            logger.warning("collection_import_file_invalid reason=%s", error)
            show_collection_import_invalid_file_error(self._parent, str(error))
            return
        logger.error("collection_import_parse_unexpected error=%s", error)
        show_collection_import_invalid_file_error(self._parent, str(error))

    def _on_worker_finished(self) -> None:
        finished = self._worker
        self._worker = None
        if finished is not None:
            finished.deleteLater()
            if not finished.wait(_WORKER_FINISH_WAIT_MS):
                logger.warning(
                    "collection_import_worker_finish_wait_timeout wait_ms=%d",
                    _WORKER_FINISH_WAIT_MS,
                )

    def _finish_import(
        self,
        collections: list[Collection],
        parse_errors: list[str],
    ) -> None:
        existing = self._request_manager.get_collections()
        decisions = self._resolve_conflicts(existing, collections)
        result = plan_collection_import(existing, collections, decisions)
        result.parse_errors.extend(parse_errors)

        apply_result = apply_imported_collections(
            self._request_manager,
            result.collections,
            result.persisted,
        )
        if getattr(apply_result, "failed_ids", None):
            result = recount_collection_import_plan(result, apply_result.failed_ids)
        save_errors = apply_result.failures if hasattr(apply_result, "failures") else apply_result
        result.parse_errors.extend(save_errors)

        self._refresh_tree()
        self._restore_tree_state()
        self._emit_collections_changed()

        logger.info(
            "collection_import_completed added_count=%d updated_count=%d "
            "skipped_count=%d renamed_count=%d request_count=%d error_count=%d",
            len(result.added),
            len(result.updated),
            len(result.skipped),
            len(result.renamed),
            result.request_count,
            len(result.parse_errors),
        )
        success = bool(result.added or result.updated or result.renamed) and not save_errors
        show_collection_import_result(
            self._parent,
            format_collection_import_result(result),
            success=success,
        )

    def _set_preparing(self, active: bool) -> None:
        self._preparing = active
        button = self._parent.findChild(QPushButton, COLLECTION_IMPORT_BUTTON)
        if button is not None:
            button.setEnabled(not active)
        if active:
            if self._show_status is not None:
                self._show_status(MSG_IMPORT_PREPARING)
            logger.debug("collection_import_busy_cue_shown")
        else:
            if self._clear_status is not None:
                self._clear_status()
            logger.debug("collection_import_busy_cue_cleared")

    def _resolve_conflicts(
        self,
        existing: list[Collection],
        candidates: list[Collection],
    ) -> dict[str, ImportConflictDecision]:
        conflicts = find_collection_conflicts(existing, candidates)
        decisions: dict[str, ImportConflictDecision] = {}
        apply_to_all: ImportConflictDecision | None = None
        for i, name in enumerate(conflicts):
            if apply_to_all is not None:
                decisions[name] = apply_to_all
                continue
            remaining_count = len(conflicts) - i - 1
            decision, use_for_all = prompt_collection_import_conflict(
                self._parent, name, remaining_count=remaining_count
            )
            decisions[name] = decision
            if use_for_all:
                apply_to_all = decision
        return decisions
