from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Callable
from pypost.models.models import RequestData
from pypost.models.response import ResponseData
from pypost.core.http_client import HTTPClient
from pypost.core.script_executor import ScriptExecutor

@dataclass
class ExecutionResult:
    response: ResponseData
    updated_variables: Dict[str, Any]
    script_logs: List[str]
    script_error: Optional[str]

class RequestService:
    def __init__(self):
        self.http_client = HTTPClient()

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
        response = self.http_client.send_request(request, variables, stream_callback, stop_flag, headers_callback)

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
