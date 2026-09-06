"""One-shot Qt worker for Library Manager service operations."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QThread, Signal


class LibraryOperationWorker(QThread):
    """Run one injected service operation without accessing widgets."""

    operation_completed = Signal(object)
    operation_failed = Signal(object)

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

    def run(self) -> None:
        """Execute the operation and report the result to the owning thread."""
        try:
            self.operation_completed.emit(self._operation(*self._args, **self._kwargs))
        except Exception as error:
            self.operation_failed.emit(error)


__all__ = ["LibraryOperationWorker"]
