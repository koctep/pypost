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
from typing import Any, cast

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
from pypost.core.collection_import_state import CollectionImportState
from pypost.core.collection_messages import (
    MSG_IMPORT_NO_VALID_COLLECTIONS,
    MSG_IMPORT_LIBRARY_NO_COLLECTIONS,
    MSG_IMPORT_LIBRARY_UNAVAILABLE,
    MSG_IMPORT_PREPARING,
    format_import_validating_message,
)
from pypost.core.import_conflicts import ImportConflictDecision
from pypost.core.metrics_protocol import MetricsTrackerProtocol, resolve_metrics
from pypost.core.qt.collection_import_parse_worker import (
    CollectionImportParseWorker,
    ReadImportFile,
)
from pypost.core.qt.library_operation_worker import LibraryOperationWorker
from pypost.core.request_manager import RequestManager
from pypost.models.models import Collection
from pypost.ui.collection_item_dialogs import (
    prompt_collection_import_conflict,
    prompt_import_collection_library,
    prompt_import_collection_file,
    prompt_library_import_mode,
    show_collection_import_invalid_file_error,
    show_collection_import_result,
)
from pypost.ui.widget_ids import (
    COLLECTION_IMPORT_BUTTON,
    COLLECTION_IMPORT_FILE_BUTTON,
    COLLECTION_IMPORT_LIBRARY_BUTTON,
)

try:
    from pypost.core.library_collection_import import LibraryCollectionImportService
except (ImportError, ModuleNotFoundError):
    LibraryCollectionImportService = None  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)

# Short join after QThread.finished so native cleanup completes before GC/delete
# (PYPOST-829 H3). Bound must stay small — slot runs on the GUI thread.
_WORKER_FINISH_WAIT_MS = 100
_FILE_IMPORT_OPERATION = "collection_import_file"
_LIBRARY_IMPORT_OPERATION = "collection_import_library"
_LIBRARY_REFRESH_OPERATION = "collection_import_refresh"


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
        metrics: MetricsTrackerProtocol | None = None,
        library_manager: object | None = None,
        library_import_service: object | None = None,
        library_selector: Callable[[QWidget, list[object]], list[object] | None]
        | None = None,
        library_mode_selector: Callable[[QWidget], object | None] | None = None,
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
        self._metrics = resolve_metrics(metrics)
        self._library_manager = library_manager
        self._library_import_service = library_import_service
        self._library_selector = library_selector
        self._library_mode_selector = library_mode_selector
        self._worker: CollectionImportParseWorker | None = None
        self._library_worker: LibraryOperationWorker | None = None
        self._state: CollectionImportState = CollectionImportState.IDLE

    def is_busy(self) -> bool:
        """True while an import is in flight (any stage but idle)."""
        return self._state is not CollectionImportState.IDLE

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
        if app is not None:
            app.processEvents()
        logger.info(
            "collection_import_wait_idle_completed elapsed_ms=%d",
            timer.elapsed(),
        )
        return True

    def teardown(self, timeout_ms: int = 5000) -> bool:
        """Safely disconnect, interrupt/wait, join, and reap background workers
        deterministically.
        """
        logger.info("collection_import_teardown_started timeout_ms=%d", timeout_ms)
        clean = True
        interruption_requested = False
        worker = self._worker
        if self.is_busy() and worker is not None and worker.isRunning():
            logger.warning("collection_import_worker_interrupting")
            worker.requestInterruption()
            interruption_requested = True
        if self.is_busy():
            clean = self.wait_idle(timeout_ms)
        worker = self._worker
        if worker is not None:
            try:
                worker.parse_progress.disconnect(self._on_parse_progress)
            except (RuntimeError, TypeError):
                pass
            try:
                worker.parse_completed.disconnect(self._on_parse_completed)
            except (RuntimeError, TypeError):
                pass
            try:
                worker.parse_failed.disconnect(self._on_parse_failed)
            except (RuntimeError, TypeError):
                pass
            try:
                worker.parse_cancelled.disconnect(self._on_parse_cancelled)
            except (RuntimeError, TypeError):
                pass
            try:
                worker.finished.disconnect(self._on_worker_finished)
            except (RuntimeError, TypeError):
                pass
            if worker.isRunning():
                logger.warning("collection_import_worker_interrupting")
                worker.requestInterruption()
                interruption_requested = True
                if not worker.wait(100):
                    clean = False
                    logger.warning("collection_import_worker_interrupt_timeout")
                else:
                    logger.info("collection_import_worker_interrupted")
            worker.deleteLater()
            logger.debug("collection_import_worker_reaped")
            self._worker = None
        elif interruption_requested:
            logger.info("collection_import_worker_interrupted")
        library_worker = self._library_worker
        if library_worker is not None:
            if library_worker.isRunning() and not library_worker.wait(timeout_ms):
                clean = False
                logger.warning("collection_library_import_worker_timeout")
            try:
                library_worker.operation_completed.disconnect()
            except (RuntimeError, TypeError):
                pass
            try:
                library_worker.operation_failed.disconnect()
            except (RuntimeError, TypeError):
                pass
            try:
                library_worker.finished.disconnect(self._on_library_worker_finished)
            except (RuntimeError, TypeError):
                pass
            library_worker.deleteLater()
            self._library_worker = None
        self._set_state(CollectionImportState.IDLE)
        app = QApplication.instance()
        if app is not None:
            app.processEvents()
        logger.info("collection_import_teardown_completed clean=%s", clean)
        return clean

    def import_collections(self) -> None:
        """Backward-compatible alias for the standalone file import flow."""
        self.import_collections_from_file()

    def import_collections_from_file(self) -> None:
        """Pick a file, parse off-thread, then finish import on the GUI thread."""
        if self.is_busy():
            logger.info("collection_import_skipped reason=busy")
            return

        path = prompt_import_collection_file(self._parent)
        if path is None:
            self._track_import_event(_FILE_IMPORT_OPERATION, "rejected")
            return

        self._start_parse(path)

    def import_collections_from_library(self) -> None:
        """Select connected library collections and apply them on the GUI thread."""
        if self.is_busy():
            logger.info("collection_library_import_skipped reason=busy")
            return

        service = self._get_library_import_service()
        if service is None:
            logger.warning("collection_library_import_unavailable reason=service_missing")
            self._track_import_event(_LIBRARY_IMPORT_OPERATION, "failure")
            show_collection_import_invalid_file_error(
                self._parent, MSG_IMPORT_LIBRARY_UNAVAILABLE
            )
            return

        list_entries = getattr(service, "list_entries", None)
        if not callable(list_entries):
            logger.warning("collection_library_import_listing_failed reason=no_service_method")
            self._track_import_event(_LIBRARY_IMPORT_OPERATION, "failure")
            show_collection_import_invalid_file_error(
                self._parent, MSG_IMPORT_LIBRARY_UNAVAILABLE
            )
            return
        self._track_import_event(_LIBRARY_IMPORT_OPERATION, "started")
        self._set_state(CollectionImportState.PREPARING)
        self._start_library_operation(
            list_entries,
            lambda entries: self._on_library_entries_listed(
                service, list(cast(list[object], entries))
            ),
        )

    def _on_library_entries_listed(self, service: object, entries: list[object]) -> None:
        """Open source and mode selectors after background library discovery."""
        if not self.is_busy():
            return
        if not any(not getattr(entry, "error", None) for entry in entries):
            diagnostics = [str(getattr(entry, "error", "Library unavailable")) for entry in entries]
            message = "\n".join([MSG_IMPORT_LIBRARY_NO_COLLECTIONS, "", *diagnostics])
            show_collection_import_invalid_file_error(self._parent, message)
            self._track_import_event(_LIBRARY_IMPORT_OPERATION, "failure")
            self._finish_library_import()
            return
        selector = self._library_selector or prompt_import_collection_library
        selected = selector(self._parent, entries)
        if not selected:
            logger.info("collection_library_import_cancelled stage=selection")
            self._track_import_event(_LIBRARY_IMPORT_OPERATION, "rejected")
            self._finish_library_import()
            return

        mode_selector = self._library_mode_selector or prompt_library_import_mode
        mode = mode_selector(self._parent)
        if mode is None:
            logger.info("collection_library_import_cancelled stage=mode")
            self._track_import_event(_LIBRARY_IMPORT_OPERATION, "rejected")
            self._finish_library_import()
            return

        self._start_library_operation(
            lambda: self._resolve_library_candidates(service, selected, mode),
            self._on_library_candidates_resolved,
        )

    def _on_library_candidates_resolved(
        self, resolved: tuple[list[Collection], list[str]]
    ) -> None:
        """Apply resolved library candidates on the GUI thread."""
        candidates, errors = resolved
        if not candidates:
            message = MSG_IMPORT_LIBRARY_NO_COLLECTIONS
            if errors:
                message = "\n".join([message, ""] + errors)
            show_collection_import_invalid_file_error(self._parent, message)
            self._track_import_event(_LIBRARY_IMPORT_OPERATION, "failure")
            self._finish_library_import()
            return
        self._set_state(CollectionImportState.APPLYING)
        self._finish_import(candidates, errors, operation=_LIBRARY_IMPORT_OPERATION)
        self._finish_library_import()

    def _on_library_operation_failed(self, error: object) -> None:
        """Report background library discovery/resolution failures safely."""
        logger.warning(
            "collection_library_import_operation_failed error_type=%s",
            type(error).__name__,
        )
        show_collection_import_invalid_file_error(
            self._parent,
            f"{MSG_IMPORT_LIBRARY_UNAVAILABLE} ({error})",
        )
        self._track_import_event(_LIBRARY_IMPORT_OPERATION, "failure")
        self._finish_library_import()

    def _start_library_operation(
        self, operation: Callable[[], Any], on_completed: Callable[[Any], None]
    ) -> None:
        worker = LibraryOperationWorker(operation)
        worker.operation_completed.connect(on_completed)
        worker.operation_failed.connect(self._on_library_operation_failed)
        worker.finished.connect(self._on_library_worker_finished)
        self._library_worker = worker
        worker.start()

    def _on_library_worker_finished(self) -> None:
        worker = self._library_worker
        self._library_worker = None
        if worker is not None:
            worker.deleteLater()

    def _finish_library_import(self) -> None:
        if self._state is not CollectionImportState.IDLE:
            self._set_state(CollectionImportState.IDLE)

    def refresh_linked_collection(self, collection_id: str) -> bool:
        """Refresh one linked active collection from its connected library source."""
        collection = next(
            (
                candidate
                for candidate in self._request_manager.get_collections()
                if candidate.id == collection_id
            ),
            None,
        )
        if collection is None or collection.library_link is None:
            logger.warning(
                "collection_library_refresh_rejected collection_id=%s reason=not_linked",
                collection_id,
            )
            self._track_import_event(_LIBRARY_REFRESH_OPERATION, "rejected")
            return False
        service = self._get_library_import_service()
        refresh = getattr(service, "refresh_linked_collection", None) if service else None
        if not callable(refresh):
            logger.warning(
                "collection_library_refresh_rejected collection_id=%s reason=service_missing",
                collection_id,
            )
            self._track_import_event(_LIBRARY_REFRESH_OPERATION, "failure")
            return False
        self._track_import_event(_LIBRARY_REFRESH_OPERATION, "started")
        try:
            refreshed = refresh(collection)
        except Exception as error:
            logger.warning(
                "collection_library_refresh_failed collection_id=%s error_type=%s",
                collection_id,
                type(error).__name__,
            )
            show_collection_import_invalid_file_error(self._parent, str(error))
            self._track_import_event(_LIBRARY_REFRESH_OPERATION, "failure")
            return False
        collections = self._request_manager.get_collections()
        index = next(
            i for i, candidate in enumerate(collections) if candidate.id == collection_id
        )
        collections[index] = refreshed
        self._request_manager.apply_loaded_collections(collections)
        self._request_manager.storage.save_collection(refreshed)
        self._refresh_tree()
        self._restore_tree_state()
        self._emit_collections_changed()
        logger.info("collection_library_refresh_completed collection_id=%s", collection_id)
        self._track_import_event(_LIBRARY_REFRESH_OPERATION, "success")
        return True

    def _get_library_import_service(self) -> object | None:
        """Return an injected service, or construct the optional core adapter lazily."""
        if self._library_import_service is not None:
            return self._library_import_service

        service_type = LibraryCollectionImportService
        if service_type is None:
            try:
                from pypost.core.library_collection_import import (
                    LibraryCollectionImportService as service_type,
                )
            except (ImportError, ModuleNotFoundError):
                return None

        manager = self._library_manager
        if manager is None:
            try:
                from pypost.core.library_manager_service import LibraryManagerService

                manager = LibraryManagerService()
            except (ImportError, ModuleNotFoundError):
                return None
        try:
            self._library_import_service = service_type(library_manager=manager)
        except Exception as error:
            logger.warning(
                "collection_library_import_service_failed error_type=%s",
                type(error).__name__,
            )
            return None
        return self._library_import_service

    @staticmethod
    def _resolve_library_candidates(
        service: object, selected: list[object], mode: object
    ) -> tuple[list[Collection], list[str]]:
        """Re-resolve selected descriptors and materialize the requested mode."""
        try:
            resolved = service.resolve_entries(selected)  # type: ignore[attr-defined]
        except Exception as error:
            logger.warning(
                "collection_library_import_resolution_failed error_type=%s",
                type(error).__name__,
            )
            return [], [f"Library collection resolution failed: {error}"]

        candidates = list(getattr(resolved, "candidates", resolved or []))
        errors = [str(error) for error in getattr(resolved, "errors", [])]
        materialize = getattr(service, "materialize_candidate", None)
        if not callable(materialize):
            return [
                candidate
                for candidate in candidates
                if isinstance(candidate, Collection)
            ], errors

        materialized: list[Collection] = []
        for candidate in candidates:
            try:
                value = materialize(candidate, mode)
            except Exception as error:
                logger.warning(
                    "collection_library_import_materialization_failed error_type=%s",
                    type(error).__name__,
                )
                errors.append(f"Library collection could not be prepared: {error}")
                continue
            if isinstance(value, Collection):
                materialized.append(value)
        return materialized, errors

    def _start_parse(self, path: Path) -> None:
        self._track_import_event(_FILE_IMPORT_OPERATION, "started")
        self._set_state(CollectionImportState.PREPARING)
        worker = CollectionImportParseWorker(path, self._read_import_file)
        worker.parse_progress.connect(self._on_parse_progress)
        worker.parse_completed.connect(self._on_parse_completed)
        worker.parse_failed.connect(self._on_parse_failed)
        worker.parse_cancelled.connect(self._on_parse_cancelled)
        worker.finished.connect(self._on_worker_finished)
        self._worker = worker
        worker.start()
        self._set_state(CollectionImportState.PARSING)
        logger.info("collection_import_parse_started path=%s", path)

    def _on_parse_progress(self, done: int, total: int) -> None:
        if self._show_status is not None:
            self._show_status(format_import_validating_message(done, total))

    def _on_parse_completed(
        self,
        collections: list[Collection],
        parse_errors: list[str],
    ) -> None:
        if not collections:
            self._set_state(CollectionImportState.IDLE)
            logger.warning("collection_import_file_invalid reason=no_valid_collections")
            self._track_import_event(_FILE_IMPORT_OPERATION, "failure")
            message = MSG_IMPORT_NO_VALID_COLLECTIONS
            if parse_errors:
                message = "\n".join([message, ""] + parse_errors)
            show_collection_import_invalid_file_error(self._parent, message)
            return
        self._set_state(CollectionImportState.APPLYING)
        self._finish_import(collections, parse_errors, operation=_FILE_IMPORT_OPERATION)

    def _on_parse_failed(self, error: object) -> None:
        self._set_state(CollectionImportState.IDLE)
        self._track_import_event(_FILE_IMPORT_OPERATION, "failure")
        if isinstance(error, CollectionImportFileError):
            logger.warning("collection_import_file_invalid reason=%s", error)
            show_collection_import_invalid_file_error(self._parent, str(error))
            return
        logger.error("collection_import_parse_unexpected error=%s", error)
        show_collection_import_invalid_file_error(self._parent, str(error))

    def _on_parse_cancelled(self) -> None:
        """A cancelled parse should look and feel like nothing happened."""
        logger.info(
            "collection_import_parse_cancelled from_state=%s",
            self._state.value,
        )
        self._track_import_event(_FILE_IMPORT_OPERATION, "rejected")
        self._set_state(CollectionImportState.IDLE)

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
        *,
        operation: str = _FILE_IMPORT_OPERATION,
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
        self._track_import_event(operation, "success" if success else "failure")
        self._set_state(CollectionImportState.IDLE)

    def _track_import_event(self, operation: str, outcome: str) -> None:
        """Record a bounded import lifecycle event when metrics are available."""
        tracker = getattr(self._metrics, "track_gui_library_operation", None)
        if callable(tracker):
            tracker(operation, outcome)

    def _set_state(self, state: CollectionImportState) -> None:
        previous = self._state
        logger.debug(
            "collection_import_state_changed from=%s to=%s",
            previous.value,
            state.value,
        )
        active = state is not CollectionImportState.IDLE
        self._state = state
        try:
            for widget_id in (
                COLLECTION_IMPORT_BUTTON,
                COLLECTION_IMPORT_FILE_BUTTON,
                COLLECTION_IMPORT_LIBRARY_BUTTON,
            ):
                button = (
                    self._parent.findChild(QPushButton, widget_id)
                    if self._parent is not None
                    else None
                )
                if button is not None:
                    button.setEnabled(not active)
        except RuntimeError:
            pass
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
