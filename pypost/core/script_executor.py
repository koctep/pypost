import contextlib
import io
import traceback
from typing import Dict, Any, Optional
from pypost.models.models import RequestData
from pypost.models.response import ResponseData

class ScriptContext:
    """
    The context object exposed to the script as 'pypost'.
    Allows interacting with environment variables and logging.
    """
    def __init__(self, variables: Dict[str, str]):
        self._variables = variables.copy()
        self._logs = []
        self._env_modified = False

    @property
    def env(self):
        return self

    def set(self, key: str, value: Any):
        """Set an environment variable."""
        self._variables[str(key)] = str(value)
        self._env_modified = True

    def get(self, key: str, default: Any = None) -> Optional[str]:
        """Get an environment variable."""
        return self._variables.get(str(key), default)
    
    def log(self, message: Any):
        """Log a message for debugging."""
        self._logs.append(str(message))

    def get_variables(self) -> Dict[str, str]:
        return self._variables

    def is_modified(self) -> bool:
        return self._env_modified
    
    def get_logs(self) -> list[str]:
        return self._logs

class ScriptExecutor:
    """
    Executes Python scripts within a controlled context.
    """
    
    @staticmethod
    def execute(script: str, request: RequestData, response: ResponseData, variables: Dict[str, str]) -> tuple[Dict[str, str], list[str], Optional[str]]:
        """
        Execute the provided script.
        
        Args:
            script: The Python script code.
            request: The request data.
            response: The response data.
            variables: Current environment variables.
            
        Returns:
            tuple: (updated_variables, logs, error_message)
            - updated_variables: The new state of variables (if modified) or None.
            - logs: List of log messages printed or logged by the script.
            - error_message: String describing an error if one occurred, else None.
        """
        if not script.strip():
            return variables, [], None

        context = ScriptContext(variables)
        
        # Prepare execution environment
        # We expose: 
        # - pypost: The context object
        # - request: RequestData (be careful, raw object)
        # - response: ResponseData
        
        local_scope = {
            'pypost': context,
            'request': request,
            'response': response
        }
        
        stdout_capture = io.StringIO()
        error_message = None

        try:
            with contextlib.redirect_stdout(stdout_capture):
                exec(script, {}, local_scope)
        except Exception:
            error_message = traceback.format_exc()
        
        logs = context.get_logs()
        captured_stdout = stdout_capture.getvalue()
        if captured_stdout:
            logs.append(f"[STDOUT] {captured_stdout}")
            
        updated_vars = context.get_variables() if context.is_modified() else None
        
        return updated_vars, logs, error_message

