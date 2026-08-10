"""Background worker for collection import file parse (PYPOST-1005)."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from pypost.core.collection_import import CollectionImportFileError
from pypost.models.models import Collection

logger = logging.getLogger(__name__)

ReadImportFile = Callable[[Path], tuple[list[Collection], list[str]]]


class CollectionImportParseWorker(QThread):
    """Run ``read_import_file(path)`` off the GUI thread."""

    parse_completed = Signal(object, object)  # collections, parse_errors
    parse_failed = Signal(object)  # CollectionImportFileError or Exception

    def __init__(self, path: Path, read_import_file: ReadImportFile) -> None:
        super().__init__()
        self._path = path
        self._read_import_file = read_import_file

    def run(self) -> None:
        logger.debug("collection_import_parse_worker_started path=%s", self._path)
        try:
            collections, parse_errors = self._read_import_file(self._path)
            logger.debug(
                "collection_import_parse_worker_completed path=%s count=%d "
                "error_count=%d",
                self._path,
                len(collections),
                len(parse_errors),
            )
            self.parse_completed.emit(collections, parse_errors)
        except CollectionImportFileError as exc:
            logger.warning(
                "collection_import_parse_worker_failed path=%s reason=%s",
                self._path,
                exc,
            )
            self.parse_failed.emit(exc)
        except Exception as exc:
            logger.error(
                "collection_import_parse_worker_failed path=%s error=%s",
                self._path,
                exc,
                exc_info=True,
            )
            self.parse_failed.emit(exc)
