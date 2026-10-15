"""Background worker for AST parsing and fold region discovery."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, ClassVar

from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import QApplication

from pypost.ui.widgets.fold.fold_region import BodyFormat
from pypost.ui.widgets.fold.structure_scanner import scan_text

if TYPE_CHECKING:
    from pypost.ui.widgets.fold.fold_region import FoldRegion

logger = logging.getLogger(__name__)


class FoldScanWorker(QThread):
    """Worker QThread offloading AST parsing for large payloads."""

    scan_completed = Signal(int, list)
    scan_failed = Signal(int, str)

    _LIVE_WORKERS: ClassVar[set[FoldScanWorker]] = set()

    def __init__(
        self,
        generation: int,
        text: str,
        body_format: BodyFormat,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._generation = generation
        self._text = text
        self._body_format = body_format
        self._interruption_requested = False
        FoldScanWorker._LIVE_WORKERS.add(self)
        self.finished.connect(self._on_worker_finished)

    def _on_worker_finished(self) -> None:
        FoldScanWorker._LIVE_WORKERS.discard(self)

    def requestInterruption(self) -> None:
        if not self._interruption_requested:
            logger.debug(
                "fold_scan_worker_interruption_requested generation=%d format=%s",
                self._generation,
                self._body_format.value,
            )
        self._interruption_requested = True
        super().requestInterruption()

    def isInterruptionRequested(self) -> bool:
        return self._interruption_requested or super().isInterruptionRequested()

    def wait(self, *args, **kwargs) -> bool:
        res = super().wait(*args, **kwargs)
        app = QApplication.instance()
        if app is not None and QThread.currentThread() == app.thread():
            app.processEvents()
        return res

    def run(self) -> None:
        start_time = time.monotonic()
        if self.isInterruptionRequested():
            duration = time.monotonic() - start_time
            logger.debug(
                "fold_scan_worker_cancelled generation=%d format=%s duration=%.4fs",
                self._generation,
                self._body_format.value,
                duration,
            )
            return
        try:
            regions: list[FoldRegion] = scan_text(
                self._text,
                self._body_format,
                is_interrupted=self.isInterruptionRequested,
            )
            duration = time.monotonic() - start_time
            if self.isInterruptionRequested():
                logger.debug(
                    "fold_scan_worker_cancelled generation=%d format=%s duration=%.4fs",
                    self._generation,
                    self._body_format.value,
                    duration,
                )
                return
            logger.debug(
                "fold_scan_worker_completed generation=%d format=%s regions=%d duration=%.4fs",
                self._generation,
                self._body_format.value,
                len(regions),
                duration,
            )
            self.scan_completed.emit(self._generation, regions)
        except Exception as exc:
            duration = time.monotonic() - start_time
            if self.isInterruptionRequested():
                logger.debug(
                    "fold_scan_worker_cancelled generation=%d format=%s duration=%.4fs",
                    self._generation,
                    self._body_format.value,
                    duration,
                )
                return
            error_msg = str(exc)
            logger.debug(
                "fold_scan_worker_failed generation=%d format=%s duration=%.4fs error=%s",
                self._generation,
                self._body_format.value,
                duration,
                error_msg,
            )
            logger.error(
                "fold_scan_worker_error generation=%d format=%s duration=%.4fs error=%s",
                self._generation,
                self._body_format.value,
                duration,
                error_msg,
            )
            self.scan_failed.emit(self._generation, error_msg)

    def __del__(self) -> None:
        try:
            if self.isRunning() and QThread.currentThread() != self:
                self.requestInterruption()
                self.wait(1000)
        except Exception:
            pass
