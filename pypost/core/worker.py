import logging
from PySide6.QtCore import QThread, Signal, QObject
from typing import Dict, List, Optional
from pypost.models.models import RequestData
from pypost.models.response import ResponseData
from pypost.core.request_service import RequestService
from pypost.core.metrics import MetricsManager
from pypost.core.history_manager import HistoryManager
from pypost.core.template_service import TemplateService

logger = logging.getLogger(__name__)

class RequestWorker(QThread):
    finished = Signal(ResponseData)
    error = Signal(str)
    env_update = Signal(dict)
    script_output = Signal(list, str) # logs, error_message
    chunk_received = Signal(str)
    headers_received = Signal(int, dict)

    def __init__(
        self,
        request_data: RequestData,
        variables: dict = None,
        metrics: MetricsManager | None = None,
        history_manager: HistoryManager | None = None,
        collection_name: str | None = None,
        template_service: TemplateService | None = None,
    ):
        super().__init__()
        self.request_data = request_data
        self.variables = variables or {}
        self._collection_name = collection_name
        if template_service is not None:
            logger.debug("RequestWorker: propagating TemplateService id=%d", id(template_service))
        self.service = RequestService(metrics=metrics, history_manager=history_manager,
                                      template_service=template_service)
        self._is_stopped = False

    def stop(self):
        """Request the worker to stop processing."""
        self._is_stopped = True

    def run(self):
        self._is_stopped = False
        try:
            # Define callback for streaming
            def on_chunk(chunk: str):
                self.chunk_received.emit(chunk)
            
            # Define callback for checking stop flag
            def check_stop():
                return self._is_stopped

            # Define callback for headers
            def on_headers(status, headers):
                self.headers_received.emit(status, headers)

            result = self.service.execute(
                self.request_data,
                self.variables,
                stream_callback=on_chunk,
                stop_flag=check_stop,
                headers_callback=on_headers,
                collection_name=self._collection_name,
                request_name=self.request_data.name,
            )
            
            if result.script_logs or result.script_error:
                self.script_output.emit(result.script_logs, result.script_error)
            
            if result.updated_variables:
                self.env_update.emit(result.updated_variables)
            
            self.finished.emit(result.response)
        except Exception as e:
            logger.error("RequestWorker failed: %s", e, exc_info=True)
            self.error.emit(str(e))
