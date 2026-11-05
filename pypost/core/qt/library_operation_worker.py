"""One-shot Qt worker for Library Manager service operations."""
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QThread, Signal

from pypost.core.cancellation import (
    CancellationTokenSource,
    OperationCancelledError,
    call_with_cancellation_token,
)

logger = logging.getLogger(__name__)


class LibraryOperationWorker(QThread):
    """Run one injected service operation without accessing widgets."""

    operation_completed = Signal(object)
    operation_failed = Signal(object)
    operation_cancelled = Signal()

    def __init__(
        self,
        operation: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__()
        self._operation = operation
        self._args = args
        self._kwargs = kwargs
        self._cancelled = False
        self._cts = CancellationTokenSource()

    def cancel(self) -> None:
        """Request cooperative stop via Qt interruption and the CTS."""
        self._cancelled = True
        self.requestInterruption()
        self._cts.cancel(reason="library operation cancelled")
        logger.debug("library_operation_worker_cancelled")

    def run(self) -> None:
        """Execute the operation and report the result to the owning thread."""
        try:
            result = call_with_cancellation_token(
                self._operation,
                *self._args,
                cancellation_token=self._cts.token,
                **self._kwargs,
            )
            if self._cancelled or self.isInterruptionRequested():
                self.operation_cancelled.emit()
                return
            self.operation_completed.emit(result)
        except OperationCancelledError:
            self.operation_cancelled.emit()
        except Exception as error:
            if self._cancelled or self.isInterruptionRequested():
                self.operation_cancelled.emit()
            else:
                self.operation_failed.emit(error)
        finally:
            self._cts.dispose()


__all__ = ["LibraryOperationWorker"]
