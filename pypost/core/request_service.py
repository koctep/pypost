import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable

logger = logging.getLogger(__name__)

from pypost.models.models import RequestData, HistoryEntry
from pypost.models.response import ResponseData
from pypost.models.errors import ErrorCategory, ExecutionError
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
    ) -> None:
        self._metrics = metrics
        self._history_manager = history_manager
        self._template_service = template_service
        if template_service is not None:
            logger.debug("RequestService: using injected TemplateService id=%d", id(template_service))
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

    def execute(
        self,
        request: RequestData,
        variables: Dict[str, Any] = None,
        stream_callback: Callable[[str], None] = None,
        stop_flag: Callable[[], bool] = None,
        headers_callback: Callable[[int, Dict], None] = None,
        collection_name: str | None = None,
        request_name: str | None = None,
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
                response = self.http_client.send_request(
                    request, variables, stream_callback, stop_flag, headers_callback
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
