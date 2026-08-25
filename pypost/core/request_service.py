from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from pypost.core.alert_manager import AlertManager, AlertPayload
from pypost.core.history_manager import HistoryManager
from pypost.core.http_client import HTTPClient, ResolvedRequestFields
from pypost.core.http_client_protocol import HTTPClientProtocol
from pypost.core.mcp_client_service import MCPClientService
from pypost.core.metrics_protocol import MetricsTrackerProtocol, resolve_metrics
from pypost.core.script_executor import ScriptExecutor
from pypost.core.sensitive_data_masking_policy import SensitiveDataMaskingPolicy
from pypost.core.template_service import TemplateService
from pypost.models.errors import ErrorCategory, ExecutionError
from pypost.models.models import HistoryEntry, RequestData
from pypost.models.response import ResponseData
from pypost.models.retry import RetryPolicy

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    response: ResponseData
    updated_variables: Dict[str, Any]
    script_logs: List[str]
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
        metrics: MetricsTrackerProtocol | None = None,
        template_service: TemplateService | None = None,
        history_manager: HistoryManager | None = None,
        alert_manager: AlertManager | None = None,
        default_retry_policy: RetryPolicy | None = None,
        http_client: HTTPClientProtocol | None = None,
        mcp_client: MCPClientService | None = None,
        max_response_bytes: int | None = None,
    ) -> None:
        self._metrics = resolve_metrics(metrics)
        self._history_manager = history_manager
        self._template_service = template_service
        self._alert_manager = alert_manager
        self._default_retry_policy = default_retry_policy
        _effective_ts = template_service or TemplateService()
        self._masking_policy = SensitiveDataMaskingPolicy(_effective_ts)
        if template_service is not None:
            logger.debug(
                "RequestService: using injected TemplateService id=%d",
                id(template_service),
            )
        logger.debug(
            "RequestService: default_retry_policy_injected=%s max_retries=%s",
            default_retry_policy is not None,
            default_retry_policy.max_retries if default_retry_policy is not None else "N/A",
        )
        if http_client is not None:
            self.http_client = http_client
            logger.debug(
                "RequestService: using injected HTTP client id=%d", id(http_client)
            )
        else:
            from pypost.core.http_client import DEFAULT_MAX_RESPONSE_BYTES

            cap = (
                max_response_bytes
                if max_response_bytes is not None
                else DEFAULT_MAX_RESPONSE_BYTES
            )
            self.http_client = HTTPClient(
                metrics=self._metrics,
                template_service=self._template_service,
                max_response_bytes=cap,
            )
        if mcp_client is not None:
            self.mcp_client = mcp_client
            logger.debug(
                "RequestService: using injected MCPClientService id=%d", id(mcp_client)
            )
        else:
            self.mcp_client = MCPClientService()

    def _execute_mcp(
        self,
        request: RequestData,
        variables: Dict[str, Any],
        headers_callback: Callable[[int, Dict], None] | None,
    ) -> tuple[ResponseData, ResolvedRequestFields]:
        url = self._template_service.render_string(request.url, variables)
        body = self._template_service.render_string(request.body, variables).strip()
        resolved_headers = {
            self._template_service.render_string(k, variables): (
                self._template_service.render_string(v, variables)
            )
            for k, v in request.headers.items()
        }
        resolved = ResolvedRequestFields(url=url, headers=resolved_headers, body=body)

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

        self._metrics.track_request_sent(request.method)
        response = self.mcp_client.run(url, operation, call_params, headers=resolved_headers)
        self._metrics.track_response_received(request.method, str(response.status_code))
        if headers_callback:
            headers_callback(response.status_code, response.headers)
        return response, resolved

    def _execute_http_with_retry(
        self,
        request: RequestData,
        variables: Dict[str, Any],
        stream_callback: Callable[[str], None] | None,
        stop_flag: Callable[[], bool] | None,
        headers_callback: Callable[[int, Dict], None] | None,
        retry_callback: Callable[[int, int, ExecutionError], None] | None,
        request_name: str,
    ) -> tuple[ResponseData, ResolvedRequestFields]:
        """Execute HTTP request with optional retry and exponential back-off."""
        policy: RetryPolicy | None = request.retry_policy
        if policy is None:
            policy = self._default_retry_policy
        _policy_source = (
            "per_request"
            if request.retry_policy is not None
            else "app_default" if self._default_retry_policy is not None else "hardcoded_fallback"
        )
        logger.debug(
            "retry_policy_resolved method=%s url=%r source=%s max_retries=%d",
            request.method,
            request.url,
            _policy_source,
            policy.max_retries if policy else 0,
        )
        max_retries = policy.max_retries if policy else 0
        delay = policy.retry_delay_seconds if policy else 1.0
        multiplier = policy.retry_backoff_multiplier if policy else 2.0
        retryable_codes = set(policy.retryable_status_codes) if policy else set()

        last_error: ExecutionError | None = None

        for attempt in range(max_retries + 1):  # attempt 0 = first try
            if stop_flag and stop_flag():
                raise ExecutionError(
                    category=ErrorCategory.CANCELLED,
                    message="Request cancelled",
                    detail="Cancelled during retry delay",
                )

            logger.debug(
                "http_attempt method=%s url=%r attempt=%d max_retries=%d",
                request.method,
                request.url,
                attempt,
                max_retries,
            )

            try:
                http_result = self.http_client.send_request(
                    request,
                    variables=variables,
                    stream_callback=stream_callback,
                    stop_flag=stop_flag,
                    headers_callback=headers_callback,
                )
                response = http_result.response
                resolved = http_result.resolved
            except ExecutionError as exc:
                if exc.category == ErrorCategory.BODY:
                    raise
                last_error = exc
                if attempt == max_retries:
                    last_error.detail = f"retries_attempted: {attempt}"
                    self._emit_exhaustion_alert(request, request_name, max_retries, last_error)
                    raise last_error
                logger.warning(
                    "retryable_error method=%s url=%r category=%s attempt=%d max_retries=%d"
                    " error=%s",
                    request.method,
                    request.url,
                    exc.category,
                    attempt,
                    max_retries,
                    exc.message,
                )
            else:
                # Response path — raises here are not caught by the handler above
                if response.status_code not in retryable_codes:
                    return response, resolved
                if attempt == max_retries:
                    last_error = ExecutionError(
                        category=ErrorCategory.NETWORK,
                        message=f"HTTP {response.status_code}",
                        detail=f"retries_attempted: {attempt}",
                    )
                    self._emit_exhaustion_alert(request, request_name, max_retries, last_error)
                    raise last_error
                logger.warning(
                    "retryable_status method=%s url=%r status=%d attempt=%d max_retries=%d",
                    request.method,
                    request.url,
                    response.status_code,
                    attempt,
                    max_retries,
                )
                last_error = ExecutionError(
                    category=ErrorCategory.NETWORK,
                    message=f"HTTP {response.status_code}",
                    detail=f"retries_attempted: {attempt}",
                )

            # Emit retry signal and track metrics
            self._metrics.track_retry_attempt(request.method, last_error.category.value)
            if retry_callback:
                retry_callback(attempt + 1, max_retries, last_error)

            # Exponential back-off (capped at 60 s)
            wait = min(delay * (multiplier**attempt), 60.0)
            logger.debug(
                "retry_backoff method=%s url=%r attempt=%d wait_seconds=%.2f",
                request.method,
                request.url,
                attempt,
                wait,
            )
            end = time.monotonic() + wait
            while time.monotonic() < end:
                if stop_flag and stop_flag():
                    logger.debug(
                        "retry_cancelled_during_backoff method=%s url=%r attempt=%d",
                        request.method,
                        request.url,
                        attempt,
                    )
                    raise ExecutionError(
                        category=ErrorCategory.CANCELLED,
                        message="Request cancelled",
                        detail="Cancelled during retry delay",
                    )
                time.sleep(0.1)

        # Defensive: loop should always return or raise (e.g. empty range(max_retries+1))
        logger.error(
            "retry_loop_invariant_failed method=%s url=%r max_retries=%d",
            request.method,
            request.url,
            max_retries,
        )
        raise ExecutionError(
            category=ErrorCategory.NETWORK,
            message="HTTP retry exhausted without recorded error",
            detail=f"retries_attempted: {max_retries}",
        )

    def _build_history_entry(
        self,
        request: RequestData,
        variables: Dict[str, Any],
        result: ExecutionResult,
        resolved_fields: ResolvedRequestFields | None,
        hidden_keys: set[str] | None,
        collection_name: str | None,
        request_name: str | None,
    ) -> tuple[HistoryEntry, int]:
        """Build a masked HistoryEntry from execution context."""
        hidden_key_count = len(hidden_keys or set())
        masked = self._masking_policy.build_history_safe_fields(
            request=request,
            variables=variables,
            hidden_keys=hidden_keys,
            resolved=resolved_fields,
        )
        entry = HistoryEntry(
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z",
            method=request.method,
            url=masked.url,
            headers=masked.headers,
            body=masked.body,
            status_code=result.response.status_code,
            response_time_ms=result.response.elapsed_time * 1000.0,
            collection_name=collection_name,
            request_name=request_name,
        )
        return entry, hidden_key_count

    def _emit_history_masking_observability(
        self,
        method: str,
        hidden_key_count: int,
    ) -> None:
        """Log and metric for sensitive-data masking during history write."""
        logger.debug(
            "history_masking_applied method=%s hidden_key_count=%d",
            method,
            hidden_key_count,
        )
        if hidden_key_count > 0:
            self._metrics.track_hidden_value_mask_applied("history")

    def _emit_history_entry_observability(self, entry: HistoryEntry) -> None:
        """Log and metric after a history entry is persisted."""
        logger.debug(
            "history_entry_recorded method=%s url=%s status=%d response_time_ms=%.1f",
            entry.method,
            entry.url,
            entry.status_code,
            entry.response_time_ms,
        )
        self._metrics.track_history_entry_appended(entry.method)

    def _record_execution_history(
        self,
        request: RequestData,
        variables: Dict[str, Any],
        result: ExecutionResult,
        resolved_fields: ResolvedRequestFields | None,
        collection_name: str | None,
        request_name: str | None,
        hidden_keys: set[str] | None,
    ) -> None:
        """Record history entry; must not raise."""
        if not self._history_manager:
            return
        try:
            entry, hidden_key_count = self._build_history_entry(
                request,
                variables,
                result,
                resolved_fields,
                hidden_keys,
                collection_name,
                request_name,
            )
            self._emit_history_masking_observability(request.method, hidden_key_count)
            self._history_manager.append(entry)
            self._emit_history_entry_observability(entry)
        except Exception as exc:
            logger.error("history_record_failed error=%s", exc)
            self._metrics.track_history_record_error()

    def _emit_exhaustion_alert(
        self,
        request: RequestData,
        request_name: str,
        retries_attempted: int,
        error: ExecutionError,
    ) -> None:
        logger.warning(
            "retry_exhausted method=%s url=%r request_name=%r retries=%d"
            " error_category=%s error=%s detail=%s",
            request.method,
            request.url,
            request_name,
            retries_attempted,
            error.category,
            error.message,
            error.detail,
        )
        self._metrics.track_request_retry_exhaustion(request.url)
        if self._alert_manager:
            self._alert_manager.emit(
                AlertPayload(
                    request_name=request_name or request.name,
                    endpoint=request.url,
                    retries_attempted=retries_attempted,
                    final_error_category=error.category.value,
                    final_error_message=error.message,
                )
            )

    def execute(
        self,
        request: RequestData,
        variables: Dict[str, Any] | None = None,
        stream_callback: Callable[[str], None] | None = None,
        stop_flag: Callable[[], bool] | None = None,
        headers_callback: Callable[[int, Dict], None] | None = None,
        collection_name: str | None = None,
        request_name: str | None = None,
        retry_callback: Callable[[int, int, ExecutionError], None] | None = None,
        hidden_keys: set[str] | None = None,
    ) -> ExecutionResult:
        """Executes a request with the given context."""
        if variables is None:
            variables = {}

        # 1. Execute request, catching structured errors
        resolved_fields: ResolvedRequestFields | None = None
        try:
            if request.method == "MCP":
                response, resolved_fields = self._execute_mcp(
                    request, variables, headers_callback
                )
            else:
                response, resolved_fields = self._execute_http_with_retry(
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
                request.method,
                request.url,
                exc.category,
                exc.detail,
            )
            if exc.category != ErrorCategory.CANCELLED:
                self._metrics.track_request_error(exc.category)
            return ExecutionResult(
                response=_error_response(exc),
                updated_variables={},
                script_logs=[],
                execution_error=exc,
            )

        updated_variables = {}
        script_logs = []
        script_error = None

        # 2. Execute post-request script if exists
        if request.post_script:
            updated_variables, script_logs, script_error = ScriptExecutor.execute(
                request.post_script, request, response, variables
            )

        exec_error_from_script = None
        if script_error:
            exec_error_from_script = ExecutionError(
                category=ErrorCategory.SCRIPT,
                message="Post-script execution failed.",
                detail=script_error,
            )
            self._metrics.track_request_error(ErrorCategory.SCRIPT)

        result = ExecutionResult(
            response=response,
            updated_variables=updated_variables,
            script_logs=script_logs,
            execution_error=exec_error_from_script,
        )

        # 3. Record history entry (must not raise)
        self._record_execution_history(
            request,
            variables,
            result,
            resolved_fields,
            collection_name,
            request_name,
            hidden_keys,
        )

        return result
