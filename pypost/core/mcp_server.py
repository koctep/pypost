import logging
from typing import List
from PySide6.QtCore import QObject, Signal

from pypost.models.models import RequestData
from pypost.core.asgi_server_host import AsgiServerHost
from pypost.core.mcp_server_impl import MCPServerImpl
from pypost.core.metrics import MetricsManager
from pypost.core.template_service import TemplateService

logger = logging.getLogger(__name__)

class MCPServerManager(QObject):
    status_changed = Signal(bool)  # True = running, False = stopped

    def __init__(self, metrics: MetricsManager | None = None,
                 template_service: TemplateService | None = None,
                 request_timeout: float = 30.0):
        super().__init__()
        self._impl = MCPServerImpl(
            metrics=metrics,
            template_service=template_service,
            request_timeout=request_timeout,
        )
        if template_service is not None:
            logger.debug(
                "MCPServerManager: propagating TemplateService id=%d",
                id(template_service),
            )
        self._server_host = AsgiServerHost("mcp", self._impl.create_app)
        self._current_port = 1080
        self._current_host = "127.0.0.1"

    def set_request_timeout(self, request_timeout: float) -> None:
        self._impl.set_request_timeout(request_timeout)

    def start_server(self, port: int, tools: List[RequestData], host: str = "127.0.0.1"):
        self._current_port = port
        self._current_host = host
        self._impl.register_tools(tools)

        self._server_host.start(host, port)
        logger.info("MCP server started on %s:%d", host, port)
        # Status emitted in thread is safer, or here if we trust it starts.
        # Let's emit here for UI responsiveness.
        self.status_changed.emit(True)

    def stop_server(self):
        if not self.is_running():
            return

        self._server_host.stop()
        logger.info("MCP server stopped")
        self.status_changed.emit(False)

    def is_running(self) -> bool:
        return self._server_host.is_running()

    def update_tools(self, tools: List[RequestData]):
        if self.is_running():
            # Restart to refresh tools
            self.stop_server()
            self.start_server(self._current_port, tools, self._current_host)
