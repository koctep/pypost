import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable

logger = logging.getLogger(__name__)

from pypost.models.models import RequestData, HistoryEntry
from pypost.models.response import ResponseData
from pypost.models.errors import ErrorCategory, ExecutionError
from pypost.models.retry import RetryPolicy
from pypost.core.alert_manager import AlertManager, AlertPayload
from pypost.core.http_client import HTTPClient
from pypost.core.mcp_client_service import MCPClientService
from pypost.core.script_executor import ScriptExecutor
from pypost.core.template_service import TemplateService
from pypost.core.metrics import MetricsManager
from pypost.core.history_manager import HistoryManager


@dataclass
class ExecutionResult:
    response: ResponseData
    updated_variables: Dict[str, Any]
    script_logs: List[str]
    script_error: Optional[str]
    execution_error: Optional[ExecutionError] = field(default=None)


def _error_response(exc: ExecutionError) -> ResponseData:
    """Synthesises a ResponseData placeholder for failed requests."""
    body = json.dumps({"error": exc.message, "detail": exc.detail})
    return ResponseData(
        status_code=0,
        headers={},
        body=body,
        elapsed_time=0.0,
        size=len(body.encode("utf-8")),
    )


class RequestService:
    def __init__(
        self,
        metrics: MetricsManager | None = None,
        template_service: TemplateService | None = None,
        history_manager: HistoryManager | None = None,
        alert_manager: AlertManager | None = None,
        default_retry_policy: RetryPolicy | None = None,
    ) -> None:
        self._metrics = metrics
        self._history_manager = history_manager
        self._template_service = template_service
        self._alert_manager = alert_manager
        self._default_retry_policy = default_retry_policy
        if template_service is not None:
            logger.debug("RequestService: using injected TemplateService id=%d", id(template_service))
        logger.debug(
            "RequestService: default_retry_policy_injected=%s max_retries=%s",
            default_retry_policy is not None,
            default_retry_policy.max_retries if default_retry_policy is not None else "N/A",
        )
        self.http_client = HTTPClient(metrics=self._metrics, template_service=self._template_service)
        self.mcp_client = MCPClientService()

    def _execute_mcp(
        self,
        request: RequestData,
        variables: Dict[str, Any],
        headers_callback: Callable[[int, Dict], None] | None,
    ) -> ResponseData:
        url = self._template_service.render_string(request.url, variables)
        body = self._template_service.render_string(request.body, variables).strip()

        operation = "list_tools"
        call_params: Dict[str, Any] | None = None

        if body:
            try:
                parsed = json.loads(body)
                if isinstance(parsed, dict) and "name" in parsed:
                    operation = "call_tool"
                    call_params = {
                        "name": parsed["name"],
                        "arguments": parsed.get("arguments") or {},
                    }
            except json.JSONDecodeError:
                pass

        if self._metrics:
            self._metrics.track_request_sent(request.method)
        response = self.mcp_client.run(url, operation, call_params)
        if self._metrics:
            self._metrics.track_response_received(
                request.method, str(response.status_code)
            )
        if headers_callback:
            headers_callback(response.status_code, response.headers)
        return response

    def _execute_http_with_retry(
        self,
        request: RequestData,
        variables: Dict[str, Any],
        stream_callback: Callable[[str], None] | None,
        stop_flag: Callable[[], bool] | None,
        headers_callback: Callable[[int, Dict], None] | None,
        retry_callback: Callable[[int, int, ExecutionError], None] | None,
        request_name: str,
    ) -> ResponseData:
        """Execute HTTP request with optional retry and exponential back-off."""
        policy: RetryPolicy | None = request.retry_policy
        if policy is None:
            policy = self._default_retry_policy
        _policy_source = (
            "per_request" if request.retry_policy is not None
            else "app_default" if self._default_retry_policy is not None
            else "hardcoded_fallback"
        )
        logger.debug(
            "retry_policy_resolved method=%s url=%r source=%s max_retries=%d",
            request.method, request.url, _policy_source, policy.max_retries if policy else 0,
        )
        max_retries = policy.max_retries if policy else 0
        delay = policy.retry_delay_seconds if policy else 1.0
        multiplier = policy.retry_backoff_multiplier if policy else 2.0
        retryable_codes = set(policy.retryable_status_codes) if policy else set()

        last_error: ExecutionError | None = None

        for attempt in range(max_retries + 1):  # attempt 0 = first try
            if stop_flag and stop_flag():
                raise ExecutionError(
                    category=ErrorCategory.NETWORK,
                    message="Request cancelled",
                    detail="Cancelled during retry delay",
                )

            logger.debug(
                "http_attempt method=%s url=%r attempt=%d max_retries=%d",
                request.method, request.url, attempt, max_retries,
            )

            try:
                response = self.http_client.send_request(
                    request,
                    variables=variables,
                    stream_callback=stream_callback,
                    stop_flag=stop_flag,
                    headers_callback=headers_callback,
                )
                if response.status_code not in retryable_codes or attempt == max_retries:
                    return response
                # Retryable status code and retries remain
                logger.warning(
                    "retryable_status method=%s url=%r status=%d attempt=%d max_retries=%d",
                    request.method, request.url, response.status_code, attempt, max_retries,
                )
                last_error = ExecutionError(
                    category=ErrorCategory.NETWORK,
                    message=f"HTTP {response.status_code}",
                    detail=f"retries_attempted: {attempt}",
                )
            except ExecutionError as exc:
                last_error = exc
                if attempt == max_retries:
                    last_error.detail = f"retries_attempted: {attempt}"
                    self._emit_exhaustion_alert(request, request_name, max_retries, last_error)
                    raise last_error
                logger.warning(
                    "retryable_error method=%s url=%r category=%s attempt=%d max_retries=%d"
                    " error=%s",
                    request.method, request.url, exc.category, attempt, max_retries, exc.message,
                )

            # Emit retry signal and track metrics
            if self._metrics:
                self._metrics.track_retry_attempt(request.method, last_error.category.value)
            if retry_callback:
                retry_callback(attempt + 1, max_retries, last_error)

            # Exponential back-off (capped at 60 s)
            wait = min(delay * (multiplier ** attempt), 60.0)
            logger.debug(
                "retry_backoff method=%s url=%r attempt=%d wait_seconds=%.2f",
                request.method, request.url, attempt, wait,
            )
            end = time.monotonic() + wait
            while time.monotonic() < end:
                if stop_flag and stop_flag():
                    logger.debug(
                        "retry_cancelled_during_backoff method=%s url=%r attempt=%d",
                        request.method, request.url, attempt,
                    )
                    raise ExecutionError(
                        category=ErrorCategory.NETWORK,
                        message="Request cancelled",
                        detail="Cancelled during retry delay",
                    )
                time.sleep(0.1)

        # Exhaustion — emit alert (retryable status code exhausted all retries)
        assert last_error is not None
        last_error.detail = f"retries_attempted: {max_retries}"
        self._emit_exhaustion_alert(request, request_name, max_retries, last_error)
        raise last_error

    def _emit_exhaustion_alert(
        self,
        request: RequestData,
        request_name: str,
        retries_attempted: int,
        error: ExecutionError,
    ) -> None:
        logger.warning(
            "retry_exhausted method=%s url=%r request_name=%r retries=%d"
            " error_category=%s error=%s",
            request.method, request.url, request_name, retries_attempted,
            error.category, error.message,
        )
        if self._metrics:
            self._metrics.track_email_notification_failure(request.url)
        if self._alert_manager:
            self._alert_manager.emit(AlertPayload(
                request_name=request_name or request.name,
                endpoint=request.url,
                retries_attempted=retries_attempted,
                final_error_category=error.category.value,
                final_error_message=error.message,
            ))

    def execute(
        self,
        request: RequestData,
        variables: Dict[str, Any] = None,
        stream_callback: Callable[[str], None] = None,
        stop_flag: Callable[[], bool] = None,
        headers_callback: Callable[[int, Dict], None] = None,
        collection_name: str | None = None,
        request_name: str | None = None,
        retry_callback: Callable[[int, int, ExecutionError], None] | None = None,
    ) -> ExecutionResult:
        """Executes a request with the given context."""
        if variables is None:
            variables = {}

        # 1. Template render guard — convert Jinja2 errors to ExecutionError(TEMPLATE)
        if self._template_service:
            try:
                self._template_service.render_string(request.url, variables)
            except Exception as exc:
                logger.error(
                    "template_render_failed url=%r detail=%s",
                    request.url, exc,
                )
                raise ExecutionError(
                    category=ErrorCategory.TEMPLATE,
                    message="Template rendering failed.",
                    detail=str(exc),
                ) from exc

        # 2. Execute request, catching structured errors
        try:
            if request.method == "MCP":
                response = self._execute_mcp(request, variables, headers_callback)
            else:
                response = self._execute_http_with_retry(
                    request,
                    variables,
                    stream_callback,
                    stop_flag,
                    headers_callback,
                    retry_callback,
                    request_name or request.name,
                )
        except ExecutionError as exc:
            logger.error(
                "request_execution_failed method=%s url=%r category=%s detail=%s",
                request.method, request.url, exc.category, exc.detail,
            )
            if self._metrics:
                self._metrics.track_request_error(exc.category)
            return ExecutionResult(
                response=_error_response(exc),
                updated_variables={},
                script_logs=[],
                script_error=None,
                execution_error=exc,
            )

        updated_variables = {}
        script_logs = []
        script_error = None

        # 3. Execute post-request script if exists
        if request.post_script:
            updated_variables, script_logs, script_error = ScriptExecutor.execute(
                request.post_script,
                request,
                response,
                variables
            )

        exec_error_from_script = None
        if script_error:
            exec_error_from_script = ExecutionError(
                category=ErrorCategory.SCRIPT,
                message="Post-script execution failed.",
                detail=script_error,
            )
            if self._metrics:
                self._metrics.track_request_error(ErrorCategory.SCRIPT)

        result = ExecutionResult(
            response=response,
            updated_variables=updated_variables,
            script_logs=script_logs,
            script_error=script_error,
            execution_error=exec_error_from_script,
        )

        # 4. Record history entry (must not raise)
        if self._history_manager:
            try:
                resolved_url = self._template_service.render_string(request.url, variables)
                resolved_headers = {
                    self._template_service.render_string(k, variables):
                    self._template_service.render_string(v, variables)
                    for k, v in request.headers.items()
                }
                resolved_body = self._template_service.render_string(request.body, variables)
                entry = HistoryEntry(
                    timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z",
                    method=request.method,
                    url=resolved_url,
                    headers=resolved_headers,
                    body=resolved_body,
                    status_code=result.response.status_code,
                    response_time_ms=result.response.elapsed_time * 1000.0,
                    collection_name=collection_name,
                    request_name=request_name,
                )
                self._history_manager.append(entry)
                logger.debug(
                    "history_entry_recorded method=%s url=%s status=%d"
                    " response_time_ms=%.1f",
                    entry.method, entry.url, entry.status_code, entry.response_time_ms,
                )
                if self._metrics:
                    self._metrics.track_history_entry_appended(entry.method)
            except Exception as exc:
                logger.error("history_record_failed error=%s", exc)
                if self._metrics:
                    self._metrics.track_history_record_error()

        return result
