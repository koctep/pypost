from PySide6.QtCore import QThread, Signal, QObject
from pypost.models.models import RequestData
from pypost.models.response import ResponseData
from pypost.core.http_client import HTTPClient

class RequestWorker(QThread):
    finished = Signal(ResponseData)
    error = Signal(str)

    def __init__(self, request_data: RequestData, variables: dict = None):
        super().__init__()
        self.request_data = request_data
        self.variables = variables or {}
        self.client = HTTPClient()

    def run(self):
        try:
            response = self.client.send_request(self.request_data, self.variables)
            self.finished.emit(response)
        except Exception as e:
            self.error.emit(str(e))
