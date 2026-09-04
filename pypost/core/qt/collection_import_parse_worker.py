"""Background worker for collection import file parse (PYPOST-1005)."""

from __future__ import annotations

import inspect
import logging
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from pypost.core.collection_import import CollectionImportFileError
from pypost.models.models import Collection

logger = logging.getLogger(__name__)

ReadImportFile = Callable[..., tuple[list[Collection], list[str]]]


class CollectionImportCancelled(Exception):
    """Raised internally to unwind a parse that was cooperatively cancelled.

    Never crosses the worker boundary as an exception -- ``run()`` catches it
    and emits ``parse_cancelled`` instead. See PYPOST-1229.
    """


def _callable_accepts_progress(func: Callable) -> bool:
    try:
        sig = inspect.signature(func)
        for p in sig.parameters.values():
            if p.kind == inspect.Parameter.VAR_KEYWORD:
                return True
            if p.name == "on_progress":
                return True
        positional = [
            p
            for p in sig.parameters.values()
            if p.kind
            in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            )
        ]
        return len(positional) >= 2
    except (ValueError, TypeError):
        return False


class CollectionImportParseWorker(QThread):
    """Run ``read_import_file(path)`` off the GUI thread."""

    parse_progress = Signal(int, int)  # done, total
    progress = parse_progress
    parse_completed = Signal(list, list)  # collections, parse_errors
    parse_failed = Signal(object)  # CollectionImportFileError or Exception
    parse_cancelled = Signal()

    def __init__(self, path: Path, read_import_file: ReadImportFile) -> None:
        super().__init__()
        self._path = path
        self._read_import_file = read_import_file

    def run(self) -> None:
        logger.debug("collection_import_parse_worker_started path=%s", self._path)
        try:
            if self.isInterruptionRequested():
                raise CollectionImportCancelled()

            def _emit_progress(done: int, total: int) -> None:
                self.parse_progress.emit(done, total)
                if self.isInterruptionRequested():
                    raise CollectionImportCancelled()

            if _callable_accepts_progress(self._read_import_file):
                collections, parse_errors = self._read_import_file(
                    self._path, on_progress=_emit_progress
                )
            else:
                collections, parse_errors = self._read_import_file(self._path)

            if self.isInterruptionRequested():
                raise CollectionImportCancelled()

            self.parse_completed.emit(collections, parse_errors)
            logger.debug(
                "collection_import_parse_worker_completed path=%s count=%d "
                "error_count=%d",
                self._path,
                len(collections),
                len(parse_errors),
            )
        except CollectionImportCancelled:
            logger.info("collection_import_parse_worker_cancelled path=%s", self._path)
            self.parse_cancelled.emit()
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
