from __future__ import annotations

import logging
import threading
import time
from typing import Literal

from PySide6.QtCore import QObject, Signal

from pypost.core.lifecycle import (
    TeardownResult,
    record_lifecycle_event,
    record_teardown_metrics,
    teardown_correlation_id,
)
from pypost.core.metrics_protocol import MetricsTrackerProtocol, resolve_metrics
from pypost.core.storage_interface import StorageInterface
from pypost.core.qt.environment_storage_worker import EnvironmentStorageWorker
from pypost.models.models import Environment

logger = logging.getLogger(__name__)

# Short join after QThread.finished so native cleanup completes before GC/delete
# (PYPOST-829 H3). Bound must stay small — slot runs on the GUI thread.
_WORKER_FINISH_WAIT_MS = 100


class EnvironmentStorageGateway(QObject):
    load_completed = Signal(list)
    load_failed = Signal(object)
    save_completed = Signal()
    save_failed = Signal(object)
    # Internal lifecycle evidence. The legacy save signals retain their
    # original signatures; this signal associates accepted update sequences
    # with the durable outcome of the save that carried them.
    save_outcome = Signal(object, str)

    def __init__(
        self,
        storage: StorageInterface,
        parent: QObject | None = None,
        metrics: MetricsTrackerProtocol | None = None,
    ) -> None:
        super().__init__(parent)
        self._storage = storage
        self._metrics = resolve_metrics(metrics)
        self._lifecycle_metric_owner = "environment_storage_gateway"
        self._worker: EnvironmentStorageWorker | None = None
        self._pending_load = False
        self._pending_save: list[Environment] | None = None
        self._pending_save_sequences: tuple[int, ...] = ()
        self._active_save_sequences: tuple[int, ...] = ()
        self._terminal_save_sequences: set[int] = set()
        self._lifecycle_lock = threading.RLock()
        self._teardown_started = False
        self._teardown_result: TeardownResult | None = None
        self._last_failure: object | None = None

    def is_busy(self) -> bool:
        with self._lifecycle_lock:
            return self._worker is not None and self._worker.isRunning()

    def has_pending_work(self) -> bool:
        with self._lifecycle_lock:
            return (
                self._worker is not None
                or self._pending_load
                or self._pending_save is not None
            )

    def wait_idle(self, timeout_ms: int = 30000) -> bool:
        from PySide6.QtCore import QElapsedTimer
        from PySide6.QtWidgets import QApplication

        if not self.has_pending_work():
            return True

        timer = QElapsedTimer()
        timer.start()
        app = QApplication.instance()
        logger.info("environment_storage_gateway_wait_idle_started")
        while self.has_pending_work():
            if timer.elapsed() >= timeout_ms:
                logger.warning(
                    "environment_storage_gateway_wait_idle_timeout elapsed_ms=%d",
                    timer.elapsed(),
                )
                return False
            if app is not None:
                app.processEvents()
            elif self._worker is not None:
                self._worker.wait(10)
        logger.info(
            "environment_storage_gateway_wait_idle_completed elapsed_ms=%d",
            timer.elapsed(),
        )
        return True

    def load_async(self) -> None:
        with self._lifecycle_lock:
            if self._teardown_started:
                logger.info("environment_storage_load_rejected reason=teardown")
                record_lifecycle_event(
                    self, "admission_rejected", metrics=self._metrics
                )
                return
            if self._worker is not None and self._worker.isRunning():
                self._pending_load = True
                logger.debug("environment_storage_gateway_load_queued")
                return
            self._start_operation("load")

    def save_async(
        self,
        environments: list[Environment],
        *,
        update_sequences: tuple[int, ...] = (),
        accepted_during_teardown: bool = False,
    ) -> None:
        coalesced: tuple[int, ...] = ()
        with self._lifecycle_lock:
            if self._teardown_started and not accepted_during_teardown:
                logger.info("environment_storage_save_rejected reason=teardown")
                record_lifecycle_event(
                    self, "admission_rejected", metrics=self._metrics
                )
                return
            snapshot = [env.model_copy(deep=True) for env in environments]
            if self._worker is not None and self._worker.isRunning():
                coalesced = self._pending_save_sequences
                self._pending_save = snapshot
                self._pending_save_sequences = tuple(update_sequences)
                logger.debug("environment_storage_gateway_save_coalesced count=%d", len(snapshot))
            else:
                self._start_operation("save", snapshot, tuple(update_sequences))
            self._terminal_save_sequences.update(coalesced)
            for sequence in coalesced:
                self._emit_save_outcome(sequence, "coalesced_into_newer_save")

    def begin_teardown(self) -> None:
        """Close storage admission before the owner starts its bounded drain."""
        with self._lifecycle_lock:
            if self._teardown_result is None:
                self._teardown_started = True

    def _start_operation(
        self,
        operation: Literal["load", "save"],
        environments: list[Environment] | None = None,
        update_sequences: tuple[int, ...] = (),
    ) -> None:
        self._active_save_sequences = update_sequences if operation == "save" else ()
        self._worker = EnvironmentStorageWorker(
            self._storage,
            operation=operation,
            environments=environments,
        )
        if operation == "load":
            self._worker.load_finished.connect(self._on_load_finished)
            self._worker.load_failed.connect(self._on_load_failed)
        else:
            self._worker.save_finished.connect(self._on_save_finished)
            self._worker.save_failed.connect(self._on_save_failed)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()
        logger.debug("environment_storage_gateway_operation_started op=%s", operation)

    def _on_load_finished(self, environments: list) -> None:
        self.load_completed.emit(environments)

    def _on_load_failed(self, error: object) -> None:
        self._last_failure = error
        self.load_failed.emit(error)

    def _on_save_finished(self) -> None:
        with self._lifecycle_lock:
            sequences = tuple(
                sequence
                for sequence in self._active_save_sequences
                if sequence not in self._terminal_save_sequences
            )
            self._terminal_save_sequences.update(sequences)
        for sequence in sequences:
            self._emit_save_outcome(sequence, "persisted")
        self.save_completed.emit()

    def _on_save_failed(self, error: object) -> None:
        self._last_failure = error
        with self._lifecycle_lock:
            sequences = tuple(
                sequence
                for sequence in self._active_save_sequences
                if sequence not in self._terminal_save_sequences
            )
            self._terminal_save_sequences.update(sequences)
        for sequence in sequences:
            self._emit_save_outcome(sequence, "failed")
        self.save_failed.emit(error)

    def _emit_save_outcome(self, sequence: int, outcome: str) -> None:
        self.save_outcome.emit(sequence, outcome)

    def teardown(self, timeout_ms: int | None = None) -> TeardownResult:
        """Close admission and drain accepted storage work within one deadline."""
        budget_ms = 5000 if timeout_ms is None else max(0, timeout_ms)
        with self._lifecycle_lock:
            if self._teardown_result is not None:
                return self._teardown_result
            started = time.monotonic()
            correlation_id = teardown_correlation_id(self)
            self._teardown_started = True
            active_count = int(self.is_busy())
            pending_count = int(self._pending_load) + int(self._pending_save is not None)
            logger.info(
                "lifecycle_teardown_started owner=environment_storage_gateway "
                "teardown_id=%s timeout_ms=%d active_count=%d pending_count=%d",
                correlation_id,
                budget_ms,
                active_count,
                pending_count,
            )
            deadline = started + budget_ms / 1000
            settled = self.wait_idle(max(0, int((deadline - time.monotonic()) * 1000)))
            if not settled:
                incomplete_sequences = set(self._active_save_sequences)
                incomplete_sequences.update(self._pending_save_sequences)
                self._terminal_save_sequences.update(incomplete_sequences)
                for sequence in incomplete_sequences:
                    self._emit_save_outcome(sequence, "incomplete")
            if settled and self._last_failure is not None:
                outcome = "failed"
                failure_kind = "worker_error"
            elif settled:
                outcome = "success"
                failure_kind = None
            else:
                outcome = "incomplete"
                failure_kind = "timeout"
            self._teardown_result = TeardownResult(
                owner="environment_storage_gateway",
                outcome=outcome,
                elapsed_ms=int((time.monotonic() - started) * 1000),
                active_count=active_count,
                pending_count=pending_count,
                failure_kind=failure_kind,
            )
            logger.info(
                "lifecycle_teardown_completed owner=environment_storage_gateway "
                "teardown_id=%s outcome=%s elapsed_ms=%d deadline_ms=%d "
                "active_count=%d pending_count=%d",
                correlation_id,
                self._teardown_result.outcome,
                self._teardown_result.elapsed_ms,
                budget_ms,
                self._teardown_result.active_count,
                self._teardown_result.pending_count,
            )
            record_teardown_metrics(self, self._teardown_result, self._metrics)
            return self._teardown_result

    def _on_worker_finished(self) -> None:
        with self._lifecycle_lock:
            finished = self._worker
            self._worker = None
            self._active_save_sequences = ()
            if finished is not None:
                finished.deleteLater()
                if not finished.wait(_WORKER_FINISH_WAIT_MS):
                    logger.warning(
                        "environment_storage_gateway_worker_finish_wait_timeout "
                        "wait_ms=%d pending_save=%s pending_load=%s",
                        _WORKER_FINISH_WAIT_MS,
                        self._pending_save is not None,
                        self._pending_load,
                    )
            if self._pending_save is not None:
                pending = self._pending_save
                pending_sequences = self._pending_save_sequences
                self._pending_save = None
                self._pending_save_sequences = ()
                logger.info(
                    "environment_storage_gateway_pending_save_started count=%d",
                    len(pending),
                )
                self._start_operation("save", pending, pending_sequences)
                return
            if self._pending_load:
                self._pending_load = False
                logger.info("environment_storage_gateway_pending_load_started")
                self._start_operation("load")
