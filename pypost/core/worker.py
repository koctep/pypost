from PySide6.QtCore import QThread, Signal, QObject
from typing import Dict, List, Optional
from pypost.models.models import RequestData
from pypost.models.response import ResponseData
from pypost.core.http_client import HTTPClient
from pypost.core.script_executor import ScriptExecutor

class RequestWorker(QThread):
    finished = Signal(ResponseData)
    error = Signal(str)
    env_update = Signal(dict)
    script_output = Signal(list, str) # logs, error_message

    def __init__(self, request_data: RequestData, variables: dict = None):
        super().__init__()
        self.request_data = request_data
        self.variables = variables or {}
        self.client = HTTPClient()

    def run(self):
        try:
            response = self.client.send_request(self.request_data, self.variables)
            
            # Execute post-request script if exists
            if self.request_data.post_script:
                updated_vars, logs, script_error = ScriptExecutor.execute(
                    self.request_data.post_script,
                    self.request_data,
                    response,
                    self.variables
                )
                
                if logs or script_error:
                    self.script_output.emit(logs, script_error)
                
                if updated_vars:
                    self.env_update.emit(updated_vars)
            
            self.finished.emit(response)
        except Exception as e:
            self.error.emit(str(e))
