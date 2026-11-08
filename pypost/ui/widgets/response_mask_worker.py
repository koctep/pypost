"""Background worker QThread for formatting medium-size JSON responses with masking."""

from __future__ import annotations

import logging
import time
from typing import Any, ClassVar, Sequence

from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import QApplication

from pypost.ui.widgets.response_mask_controller import (
    format_masked_json,
)

logger = logging.getLogger(__name__)


class ResponseMaskWorker(QThread):
    """Worker QThread offloading JSON masking and token span discovery for medium payloads."""

    formatting_completed = Signal(int, str, list)  # (generation, formatted_text, spans)
    formatting_failed = Signal(int, str)  # (generation, raw_body)

    _LIVE_WORKERS: ClassVar[set[ResponseMaskWorker]] = set()

    def __init__(
        self,
        generation: int,
        raw_body: str,
        hidden_fields: Sequence[str],
        indent: int = 2,
        parent: QObject | None = None,
    ) -> None:
        """Initialize worker with target payload and masking configuration."""
        super().__init__(parent)
        self._generation = generation
        self._raw_body = raw_body
        self._hidden_fields = tuple(hidden_fields)
        self._indent = indent
        self._interruption_requested = False
        ResponseMaskWorker._LIVE_WORKERS.add(self)
        self.finished.connect(self._on_worker_finished)
        self.destroyed.connect(self._on_worker_destroyed)

    def _on_worker_finished(self) -> None:
        """Discard completed worker instance from live worker registry."""
        ResponseMaskWorker._LIVE_WORKERS.discard(self)

    def _on_worker_destroyed(self, obj: object | None = None) -> None:
        """Discard destroyed worker instance from live worker registry."""
        ResponseMaskWorker._LIVE_WORKERS.discard(self)

    def requestInterruption(self) -> None:
        """Request cooperative cancellation of worker thread execution."""
        if not self._interruption_requested:
            logger.debug(
                "response_mask_worker_interruption_requested generation=%d",
                self._generation,
            )
        self._interruption_requested = True
        super().requestInterruption()

    def isInterruptionRequested(self) -> bool:
        """Check whether cancellation was requested on this worker instance."""
        return self._interruption_requested or super().isInterruptionRequested()

    def wait(self, *args: Any, **kwargs: Any) -> bool:
        """Wait for worker thread exit while pumping main event loop if called from UI thread."""
        res = super().wait(*args, **kwargs)
        app = QApplication.instance()
        if app is not None and QThread.currentThread() == app.thread():
            app.processEvents()
        return res

    def run(self) -> None:
        """Format JSON and discover masked token spans in background thread."""
        start_time = time.monotonic()
        logger.debug(
            "response_mask_worker_started generation=%d chars=%d selectors_count=%d",
            self._generation,
            len(self._raw_body),
            len(self._hidden_fields),
        )
        if self.isInterruptionRequested():
            logger.debug(
                "response_mask_worker_cancelled generation=%d chars=%d",
                self._generation,
                len(self._raw_body),
            )
            return

        try:
            formatted_text, spans = format_masked_json(
                self._raw_body,
                self._hidden_fields,
                indent=self._indent,
            )
            if self.isInterruptionRequested():
                logger.debug(
                    "response_mask_worker_cancelled generation=%d chars=%d",
                    self._generation,
                    len(self._raw_body),
                )
                return

            duration = time.monotonic() - start_time
            logger.debug(
                "response_mask_worker_completed generation=%d spans=%d duration=%.4fs",
                self._generation,
                len(spans),
                duration,
            )
            self.formatting_completed.emit(self._generation, formatted_text, spans)
        except Exception as exc:
            if self.isInterruptionRequested():
                logger.debug(
                    "response_mask_worker_cancelled generation=%d chars=%d",
                    self._generation,
                    len(self._raw_body),
                )
                return

            duration = time.monotonic() - start_time
            logger.warning(
                "response_mask_worker_failed generation=%d chars=%d duration=%.4fs error=%s",
                self._generation,
                len(self._raw_body),
                duration,
                type(exc).__name__,
            )
            self.formatting_failed.emit(self._generation, self._raw_body)

    def __del__(self) -> None:
        """Ensure running background thread is requested to interrupt upon teardown."""
        try:
            if self.isRunning() and QThread.currentThread() != self:
                self.requestInterruption()
                self.wait(1000)
        except Exception:
            pass
