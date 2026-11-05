"""Background worker for remote collection fetch during variable import."""
from __future__ import annotations

import logging
from typing import Any

from PySide6.QtCore import QObject, QThread, Signal

logger = logging.getLogger(__name__)


class CollectionFetchWorker(QThread):
    """Background worker for non-blocking remote collection retrieval."""

    fetch_completed = Signal(object, int)
    fetch_failed = Signal(Exception, int)

    def __init__(
        self,
        library_service: Any,
        connection_id: str,
        collection_path: str,
        generation_id: int,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.library_service = library_service
        self.connection_id = connection_id
        self.collection_path = collection_path
        self.generation_id = generation_id
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True
        self.requestInterruption()
        logger.debug(
            "collection_variable_fetch_worker_cancelled generation_id=%d connection_id=%s",
            self.generation_id,
            self.connection_id,
        )

    def run(self) -> None:
        logger.debug(
            "collection_variable_fetch_worker_started generation_id=%d connection_id=%s path=%s",
            self.generation_id,
            self.connection_id,
            self.collection_path,
        )
        try:
            col = self.library_service.read_collection(
                self.connection_id,
                self.collection_path,
            )
            if not self._cancelled and not self.isInterruptionRequested():
                logger.debug(
                    "collection_variable_fetch_worker_completed generation_id=%d",
                    self.generation_id,
                )
                self.fetch_completed.emit(col, self.generation_id)
            else:
                logger.debug(
                    "collection_variable_fetch_worker_interrupted generation_id=%d",
                    self.generation_id,
                )
        except Exception as exc:
            if not self._cancelled and not self.isInterruptionRequested():
                logger.warning(
                    "collection_variable_fetch_worker_failed generation_id=%d error=%s",
                    self.generation_id,
                    exc,
                )
                self.fetch_failed.emit(exc, self.generation_id)
            else:
                logger.debug(
                    "collection_variable_fetch_worker_interrupted_on_error generation_id=%d "
                    "error=%s",
                    self.generation_id,
                    exc,
                )
