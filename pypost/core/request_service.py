import json
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Callable

from pypost.models.models import RequestData
from pypost.models.response import ResponseData
from pypost.core.http_client import HTTPClient
from pypost.core.mcp_client_service import MCPClientService
from pypost.core.script_executor import ScriptExecutor
from pypost.core.template_service import template_service
from pypost.core.metrics import MetricsManager


@dataclass
class ExecutionResult:
    response: ResponseData
    updated_variables: Dict[str, Any]
    script_logs: List[str]
    script_error: Optional[str]

class RequestService:
    def __init__(self):
        self.http_client = HTTPClient()
        self.mcp_client = MCPClientService()

    def _execute_mcp(
        self,
        request: RequestData,
        variables: Dict[str, Any],
        headers_callback: Callable[[int, Dict], None] | None,
    ) -> ResponseData:
        url = template_service.render_string(request.url, variables)
        body = template_service.render_string(request.body, variables).strip()

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

        MetricsManager().track_request_sent(request.method)
        response = self.mcp_client.run(url, operation, call_params)
        MetricsManager().track_response_received(
            request.method, str(response.status_code)
        )
        if headers_callback:
            headers_callback(response.status_code, response.headers)
        return response

    def execute(self, request: RequestData, variables: Dict[str, Any] = None, 
                stream_callback: Callable[[str], None] = None,
                stop_flag: Callable[[], bool] = None,
                headers_callback: Callable[[int, Dict], None] = None) -> ExecutionResult:
        """
        Executes a request with the given context.
        """
        if variables is None:
            variables = {}

        # 1. Execute request
        if request.method == "MCP":
            response = self._execute_mcp(request, variables, headers_callback)
        else:
            response = self.http_client.send_request(
                request, variables, stream_callback, stop_flag, headers_callback
            )

        updated_variables = {}
        script_logs = []
        script_error = None

        # 2. Execute post-request script if exists
        if request.post_script:
            updated_variables, script_logs, script_error = ScriptExecutor.execute(
                request.post_script,
                request,
                response,
                variables
            )

        return ExecutionResult(
            response=response,
            updated_variables=updated_variables,
            script_logs=script_logs,
            script_error=script_error
        )
