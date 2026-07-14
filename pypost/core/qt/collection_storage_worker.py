from __future__ import annotations

import logging

from PySide6.QtCore import QThread, Signal

from pypost.core.storage_interface import StorageInterface

logger = logging.getLogger(__name__)


class CollectionStorageWorker(QThread):
    load_finished = Signal(list)
    load_failed = Signal(object)

    def __init__(self, storage: StorageInterface) -> None:
        super().__init__()
        self._storage = storage

    def run(self) -> None:
        logger.debug("collection_storage_worker_run_started")
        try:
            collections = self._storage.load_collections()
            logger.debug(
                "collection_storage_worker_load_completed count=%d",
                len(collections),
            )
            self.load_finished.emit(collections)
        except Exception as exc:
            logger.error(
                "collection_storage_worker_load_failed error=%s",
                exc,
                exc_info=True,
            )
            self.load_failed.emit(exc)
