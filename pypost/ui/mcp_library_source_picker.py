"""Qt-light asynchronous library source selection facade."""
from __future__ import annotations

import logging
import time
from typing import Any, Callable

from pypost.core.metrics_protocol import MetricsTrackerProtocol, resolve_metrics
from pypost.core.qt.library_operation_worker import LibraryOperationWorker

logger = logging.getLogger(__name__)


class LibraryMcpSourcePicker:
    """Own request identity and cancellation, independent of widget lifetime."""

    def __init__(
        self, *, library_service: Any, worker_factory: Callable[..., Any] | None = None,
        metrics: MetricsTrackerProtocol | None = None
    ):
        self.library_service = library_service
        self._metrics = resolve_metrics(metrics)
        self.worker_factory = worker_factory or (
            lambda operation: LibraryOperationWorker(operation)
        )
        self.busy = False
        self.selected_collection: dict[str, Any] | None = None
        self.overlay_writes: list[Any] = []
        self._request = 0
        self._worker: Any = None
        self._on_complete: Any = None
        self._on_error: Any = None
        self._started_at = 0.0
        self._operation = ""

    @property
    def active_request_id(self) -> int | None:
        """Return the request still allowed to deliver a result."""
        return self._request if self.busy else None

    def begin_manifest_listing(self, library_id: str, on_complete=None, on_error=None) -> int:
        self._request += 1
        request_id = self._request
        self._cancel_worker()
        self.busy = True
        self._started_at = time.monotonic()
        self._operation = "collections"
        logger.info("mcp_library_discovery_started operation=collections library_id=%s", library_id)
        self.selected_collection = None
        self._on_complete = on_complete
        self._on_error = on_error
        worker = self.worker_factory(
            lambda: self._list_manifest_collections(library_id)
        )
        self._worker = worker
        if hasattr(worker, "operation_completed"):
            worker.operation_completed.connect(
                lambda result: self._complete(request_id, result)
            )
            worker.operation_failed.connect(lambda error: self._failed(request_id, error))
            worker.start()
        else:
            start_method: Any = getattr(worker, "start")
            start_method(lambda result: self._complete(request_id, result))
        return request_id

    def begin_library_listing(self, on_complete=None, on_error=None) -> int:
        """Discover connected library records through the same cancellable worker."""
        self._request += 1
        request_id = self._request
        self._cancel_worker()
        self.busy = True
        self._started_at = time.monotonic()
        self._operation = "libraries"
        logger.info("mcp_library_discovery_started operation=libraries")
        self._on_complete = on_complete
        self._on_error = on_error
        worker = self.worker_factory(lambda: self.library_service.list_connections())
        self._worker = worker
        if hasattr(worker, "operation_completed"):
            worker.operation_completed.connect(
                lambda result: self._complete(request_id, result)
            )
            worker.operation_failed.connect(
                lambda error: self._failed(request_id, error)
            )
            worker.start()
        else:
            start_method: Any = getattr(worker, "start")
            start_method(lambda result: self._complete(request_id, result))
        return request_id

    def cancel(self, request_id: int) -> None:
        if request_id == self._request:
            self._record_discovery("cancelled", 0)
            logger.info("mcp_library_discovery_cancelled operation=%s", self._operation)
            self._request += 1
            self.busy = False
            self.selected_collection = None
            self._on_complete = None
            self._on_error = None
            self._cancel_worker()

    def cancel_active(self) -> None:
        """Cancel the active request, if any, and invalidate its callbacks."""
        if self.busy:
            self._record_discovery("cancelled", 0)
            logger.info("mcp_library_discovery_cancelled operation=%s", self._operation)
        self._request += 1
        self.busy = False
        self.selected_collection = None
        self._on_complete = None
        self._on_error = None
        self._cancel_worker()

    def _cancel_worker(self) -> None:
        if self._worker is not None and hasattr(self._worker, "cancel"):
            self._worker.cancel()
        self._worker = None

    def _list_manifest_collections(self, library_id: str) -> Any:
        method = getattr(self.library_service, "list_manifest_collections", None)
        if not callable(method):
            raise ValueError("library_invalid: connected library service cannot list collections")
        return method(library_id)

    def _complete(self, request_id: int, result: Any) -> None:
        if request_id != self._request:
            return
        self.busy = False
        count = len(result) if isinstance(result, (list, tuple)) else 0
        self._record_discovery("success", count)
        logger.info(
            "mcp_library_discovery_completed operation=%s item_count=%d", self._operation, count
        )
        self.selected_collection = result
        callback = self._on_complete
        self._on_complete = None
        self._on_error = None
        if callback is not None:
            callback(result)

    def _failed(self, request_id: int, error: Exception) -> None:
        if request_id == self._request:
            self.busy = False
            self._record_discovery("failure", 0)
            logger.warning(
                "mcp_library_discovery_failed operation=%s error_type=%s",
                self._operation, type(error).__name__,
            )
            callback = self._on_error
            self._on_complete = None
            self._on_error = None
            if callback is not None:
                callback(error)

    def _record_discovery(self, outcome: str, item_count: int) -> None:
        self._metrics.track_mcp_library_discovery(
            self._operation, outcome, time.monotonic() - self._started_at, item_count
        )
