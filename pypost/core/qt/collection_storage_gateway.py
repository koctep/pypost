from __future__ import annotations

import logging

from PySide6.QtCore import QObject, Signal

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

    def is_busy(self) -> bool:
        return self._worker is not None and self._worker.isRunning()

    def has_pending_work(self) -> bool:
        return self.is_busy() or self._pending_load

    def load_async(self) -> None:
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
        self.load_completed.emit(collections)

    def _on_load_failed(self, error: object) -> None:
        self.load_failed.emit(error)

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
