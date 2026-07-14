import logging
import threading

from PySide6.QtCore import QThread, Signal

from pypost.core.alert_manager import AlertManager
from pypost.core.history_manager import HistoryManager
from pypost.core.metrics_protocol import MetricsTrackerProtocol
from pypost.core.execute_request_protocol import ExecuteRequestProtocol
from pypost.core.request_service import RequestService
from pypost.core.template_service import TemplateService
from pypost.models.errors import ErrorCategory, ExecutionError
from pypost.models.models import RequestData
from pypost.models.response import ResponseData
from pypost.models.retry import RetryPolicy

logger = logging.getLogger(__name__)


class RequestWorker(QThread):
    """Execute one HTTP/MCP request on a background thread.

    One-shot lifecycle: allocate a new instance per send. After ``stop()`` sets the
    cooperative cancel flag, the instance must not be reused — ``_stop_event`` is never
    cleared. ``TabsPresenter`` follows this by creating a fresh worker for each request.
    """

    finished = Signal(ResponseData)
    error = Signal(object)  # carries ExecutionError; falls back to str for cancellation
    retry_attempt = Signal(int, int, object)  # attempt, max_retries, ExecutionError
    env_update = Signal(dict)
    script_output = Signal(list, str)  # logs, error_message
    chunk_received = Signal(str)
    headers_received = Signal(int, dict)

    def __init__(
        self,
        request_data: RequestData,
        variables: dict = None,
        hidden_keys: set[str] | None = None,
        metrics: MetricsTrackerProtocol | None = None,
        history_manager: HistoryManager | None = None,
        collection_name: str | None = None,
        template_service: TemplateService | None = None,
        alert_manager: AlertManager | None = None,
        default_retry_policy: RetryPolicy | None = None,
        max_response_bytes: int | None = None,
    ):
        super().__init__()
        self.request_data = request_data
        self.variables = variables or {}
        self.hidden_keys = hidden_keys or set()
        self._collection_name = collection_name
        if template_service is not None:
            logger.debug("RequestWorker: propagating TemplateService id=%d", id(template_service))
        logger.debug(
            "RequestWorker: alert_manager_injected=%s id=%s",
            alert_manager is not None,
            id(alert_manager) if alert_manager is not None else "None",
        )
        logger.debug(
            "RequestWorker: default_retry_policy_injected=%s max_retries=%s",
            default_retry_policy is not None,
            default_retry_policy.max_retries if default_retry_policy is not None else "N/A",
        )
        self.service: ExecuteRequestProtocol = RequestService(
            metrics=metrics,
            history_manager=history_manager,
            template_service=template_service,
            alert_manager=alert_manager,
            default_retry_policy=default_retry_policy,
            max_response_bytes=max_response_bytes,
        )
        self._stop_event = threading.Event()

    def stop(self):
        """Request cooperative cancellation of the in-flight execution.

        Sets ``_stop_event`` permanently for this instance. Do not call ``start()`` again
        on this worker; create a new ``RequestWorker`` for subsequent sends.
        """
        logger.debug(
            "worker_stop_requested method=%s url=%s",
            self.request_data.method,
            self.request_data.url,
        )
        self._stop_event.set()

    def run(self):
        logger.debug(
            "worker_run_started method=%s url=%s request_id=%s",
            self.request_data.method,
            self.request_data.url,
            self.request_data.id,
        )
        try:
            # Define callback for streaming
            def on_chunk(chunk: str):
                self.chunk_received.emit(chunk)

            # Define callback for checking stop flag
            def check_stop():
                return self._stop_event.is_set()

            # Define callback for headers
            def on_headers(status, headers):
                self.headers_received.emit(status, headers)

            # Define callback for retry progress
            def on_retry(attempt: int, max_retries: int, err: ExecutionError) -> None:
                self.retry_attempt.emit(attempt, max_retries, err)

            result = self.service.execute(
                self.request_data,
                self.variables,
                stream_callback=on_chunk,
                stop_flag=check_stop,
                headers_callback=on_headers,
                collection_name=self._collection_name,
                request_name=self.request_data.name,
                retry_callback=on_retry,
                hidden_keys=self.hidden_keys,
            )

            script_err = None
            if (
                result.execution_error
                and result.execution_error.category == ErrorCategory.SCRIPT
            ):
                script_err = result.execution_error.detail
            if result.script_logs or script_err:
                self.script_output.emit(result.script_logs, script_err)

            if result.updated_variables:
                self.env_update.emit(result.updated_variables)

            if (
                result.execution_error
                and result.execution_error.category == ErrorCategory.CANCELLED
            ):
                logger.debug(
                    "worker_run_cancelled method=%s url=%s",
                    self.request_data.method,
                    self.request_data.url,
                )
                self.error.emit(result.execution_error)
                return

            stopped = self._stop_event.is_set()
            logger.debug(
                "worker_run_completed method=%s url=%s stopped=%s",
                self.request_data.method,
                self.request_data.url,
                stopped,
            )
            self.finished.emit(result.response)
        except Exception as exc:
            logger.error("RequestWorker unexpected error: %s", exc, exc_info=True)
            self.error.emit(
                ExecutionError(
                    category=ErrorCategory.UNKNOWN,
                    message="An unexpected error occurred.",
                    detail=str(exc),
                )
            )
