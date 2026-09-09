from __future__ import annotations

import logging
import time

from PySide6.QtCore import QElapsedTimer, QObject, Signal
from PySide6.QtWidgets import QApplication

from pypost.core.lifecycle import TeardownResult
from pypost.core.qt.collection_storage_worker import CollectionStorageWorker
from pypost.core.storage_interface import StorageInterface

logger = logging.getLogger(__name__)

# Short join after QThread.finished so native cleanup completes before GC/delete
# (PYPOST-829 H3). Bound must stay small — slot runs on the GUI thread.
_WORKER_FINISH_WAIT_MS = 100


class CollectionStorageGateway(QObject):
    load_completed = Signal(list)
    load_failed = Signal(object)

    def __init__(self, storage: StorageInterface, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._storage = storage
        self._worker: CollectionStorageWorker | None = None
        self._pending_load = False
        self._teardown_started = False
        self._teardown_result: TeardownResult | None = None

    def is_busy(self) -> bool:
        return self._worker is not None and self._worker.isRunning()

    def has_pending_work(self) -> bool:
        return self.is_busy() or self._pending_load

    def load_async(self) -> None:
        if self._teardown_started:
            logger.info("collection_storage_load_rejected reason=teardown")
            return
        if self.is_busy():
            self._pending_load = True
            logger.debug("collection_storage_gateway_load_queued")
            return
        self._start_load()

    def _start_load(self) -> None:
        self._worker = CollectionStorageWorker(self._storage)
        self._worker.load_finished.connect(self._on_load_finished)
        self._worker.load_failed.connect(self._on_load_failed)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()
        logger.debug("collection_storage_gateway_load_started")

    def _on_load_finished(self, collections: list) -> None:
        if not self._teardown_started:
            self.load_completed.emit(collections)

    def _on_load_failed(self, error: object) -> None:
        if not self._teardown_started:
            self.load_failed.emit(error)

    def teardown(self, timeout_ms: int = 5000) -> TeardownResult:
        """Fence callbacks and wait for the startup storage worker."""
        if self._teardown_result is not None:
            return self._teardown_result
        started = time.monotonic()
        budget_ms = max(0, timeout_ms)
        active_count = int(self.is_busy())
        pending_count = int(self._pending_load)
        self._teardown_started = True
        self._pending_load = False
        timer = QElapsedTimer()
        timer.start()
        app = QApplication.instance()
        while self._worker is not None and timer.elapsed() < budget_ms:
            if app is not None:
                app.processEvents()
            worker = self._worker
            if worker is not None:
                worker.wait(min(10, max(0, budget_ms - timer.elapsed())))
        settled = self._worker is None or not self._worker.isRunning()
        self._teardown_result = TeardownResult(
            owner="collection_storage_gateway",
            outcome="success" if settled else "incomplete",
            elapsed_ms=int((time.monotonic() - started) * 1000),
            active_count=active_count,
            pending_count=pending_count,
            failure_kind=None if settled else "timeout",
        )
        return self._teardown_result

    def _on_worker_finished(self) -> None:
        finished = self._worker
        self._worker = None
        if finished is not None:
            finished.deleteLater()
            if not finished.wait(_WORKER_FINISH_WAIT_MS):
                logger.warning(
                    "collection_storage_gateway_worker_finish_wait_timeout "
                    "wait_ms=%d pending_load=%s",
                    _WORKER_FINISH_WAIT_MS,
                    self._pending_load,
                )
        if self._pending_load:
            self._pending_load = False
            logger.info("collection_storage_gateway_pending_load_started")
            self._start_load()
