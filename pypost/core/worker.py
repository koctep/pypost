from PySide6.QtCore import QThread, Signal, QObject
from typing import Dict, List, Optional
from pypost.models.models import RequestData
from pypost.models.response import ResponseData
from pypost.core.request_service import RequestService

class RequestWorker(QThread):
    finished = Signal(ResponseData)
    error = Signal(str)
    env_update = Signal(dict)
    script_output = Signal(list, str) # logs, error_message

    def __init__(self, request_data: RequestData, variables: dict = None):
        super().__init__()
        self.request_data = request_data
        self.variables = variables or {}
        self.service = RequestService()

    def run(self):
        try:
            result = self.service.execute(self.request_data, self.variables)
            
            if result.script_logs or result.script_error:
                self.script_output.emit(result.script_logs, result.script_error)
            
            if result.updated_variables:
                self.env_update.emit(result.updated_variables)
            
            self.finished.emit(result.response)
        except Exception as e:
            self.error.emit(str(e))
