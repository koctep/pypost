"""Owns request workers: construction, cancellation, disposal and teardown.

Everything about a request in flight lives here. The presenter reacts to the
signals below and updates the tab it opened the request from; it does not hold a
worker, and does not know that a QThread is involved.

Requests are addressed by an opaque key -- the presenter passes the tab -- so a
caller can cancel or release one without a reference to the thread running it.
"""
import logging
from typing import Callable

from PySide6.QtCore import QObject, Signal

from pypost.core.alert_manager import AlertManager
from pypost.core.history_manager import HistoryManager
from pypost.core.metrics import MetricsManager
from pypost.core.template_service import TemplateService
from pypost.core.worker import RequestWorker
from pypost.models.models import RequestData
from pypost.models.settings import AppSettings

logger = logging.getLogger(__name__)

# How long teardown waits for a cancelled request worker to unwind.
WORKER_SHUTDOWN_TIMEOUT_MS = 3000


class RequestExecution(QObject):
    started = Signal(object)                        # key
    cancelling = Signal(object)                     # key
    finished = Signal(object, object)               # key, ResponseData
    failed = Signal(object, object)                 # key, ExecutionError | str
    script_output = Signal(object, object, object)  # key, logs, error
    headers_received = Signal(object, int, dict)    # key, status, headers
    chunk_received = Signal(object, str)            # key, text
    retry_attempt = Signal(object, int, int)        # key, attempt, max_retries
    env_update = Signal(object)                     # dict

    def __init__(
        self,
        settings: AppSettings,
        metrics: MetricsManager | None = None,
        history_manager: HistoryManager | None = None,
        template_service: TemplateService | None = None,
        alert_manager: AlertManager | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._settings = settings
        self._metrics = metrics
        self._history_manager = history_manager
        self._template_service = template_service
        self._alert_manager = alert_manager
        self._variables: dict = {}
        # Addressed by key while running, and held separately until the thread
        # ends so a request whose tab was closed is still joined at teardown.
        self._by_key: dict[object, RequestWorker] = {}
        self._active: set[RequestWorker] = set()

    def apply_settings(self, settings: AppSettings) -> None:
        """Later requests use these; ones already in flight keep what they started with."""
        self._settings = settings

    def set_variables(self, variables: dict) -> None:
        self._variables = variables

    def is_running(self, key: object) -> bool:
        worker = self._by_key.get(key)
        return worker is not None and worker.isRunning()

    def send(
        self,
        key: object,
        request_data: RequestData,
        collection_name: str | None = None,
    ) -> None:
        """Start the request, or cancel the one already running under this key.

        The send control is the same control as the stop control, so the caller
        does not decide which of the two this is; it reacts to `started` or
        `cancelling`.
        """
        if self._clear_if_finished(key):
            logger.debug(
                "stale_worker_cleared method=%s url=%s",
                request_data.method, request_data.url,
            )

        if self.is_running(key):
            logger.info(
                "request_stop_requested method=%s url=%s",
                request_data.method, request_data.url,
            )
            self._by_key[key].stop()
            self.cancelling.emit(key)
            return

        logger.info(
            "request_send_initiated method=%s url=%s request_id=%s",
            request_data.method, request_data.url, request_data.id,
        )
        worker = self._build_worker(key, request_data, collection_name)
        self._by_key[key] = worker
        self._active.add(worker)
        self.started.emit(key)
        worker.start()

    def release(self, key: object, on_finished: Callable[[], None]) -> bool:
        """Cancel the request under `key` and run `on_finished` once it ends.

        Returns False when nothing was running, in which case the caller should
        do its own cleanup straight away.
        """
        worker = self._by_key.get(key)
        if worker is None or not worker.isRunning():
            self._by_key.pop(key, None)
            return False

        worker.stop()
        # QThread.finished, not the result signals: it fires on every outcome.
        worker.finished.connect(on_finished)
        self._by_key.pop(key, None)
        return True

    def shutdown(self) -> None:
        """Cancel and join every request still running, before teardown."""
        workers = [worker for worker in self._active if worker.isRunning()]

        for worker in workers:
            worker.stop()
        abandoned = 0
        for worker in workers:
            # Bounded: cancellation is cooperative and a worker blocked in a socket
            # read cannot honour it, so an unbounded join holds the quit for as long
            # as the request would have taken.
            if not worker.wait(WORKER_SHUTDOWN_TIMEOUT_MS):
                abandoned += 1

        if workers:
            logger.info(
                "request_workers_shutdown count=%d abandoned=%d",
                len(workers), abandoned,
            )
        if abandoned:
            logger.warning(
                "request_workers_shutdown_timeout count=%d timeout_ms=%d",
                abandoned, WORKER_SHUTDOWN_TIMEOUT_MS,
            )

    def _clear_if_finished(self, key: object) -> bool:
        worker = self._by_key.get(key)
        if worker is not None and not worker.isRunning():
            del self._by_key[key]
            return True
        return False

    def _build_worker(
        self,
        key: object,
        request_data: RequestData,
        collection_name: str | None,
    ) -> RequestWorker:
        worker = RequestWorker(
            request_data,
            variables=self._variables,
            metrics=self._metrics,
            history_manager=self._history_manager,
            collection_name=collection_name,
            template_service=self._template_service,
            alert_manager=self._alert_manager,
            default_retry_policy=self._settings.default_retry_policy,
            request_timeout=self._settings.request_timeout,
        )
        worker.request_finished.connect(
            lambda response: self.finished.emit(key, response)
        )
        worker.error.connect(lambda error: self.failed.emit(key, error))
        worker.env_update.connect(self.env_update.emit)
        worker.script_output.connect(
            lambda logs, err: self.script_output.emit(key, logs, err)
        )
        worker.chunk_received.connect(
            lambda chunk: self.chunk_received.emit(key, chunk)
        )
        worker.headers_received.connect(
            lambda status, headers: self.headers_received.emit(key, status, headers)
        )
        worker.retry_attempt.connect(
            lambda attempt, max_retries, _err: self.retry_attempt.emit(
                key, attempt, max_retries
            )
        )
        # Disposal hangs off the thread's own completion rather than the result
        # signals: those fire from inside run(), and neither covers every outcome.
        worker.finished.connect(worker.deleteLater)
        worker.finished.connect(lambda w=worker: self._forget(key, w))
        return worker

    def _forget(self, key: object, worker: RequestWorker) -> None:
        self._active.discard(worker)
        if self._by_key.get(key) is worker:
            del self._by_key[key]
