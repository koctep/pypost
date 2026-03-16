import logging
import threading
import uvicorn
import asyncio
import time
from typing import List, Optional
from PySide6.QtCore import QObject, Signal

from pypost.models.models import RequestData
from pypost.core.mcp_server_impl import MCPServerImpl
from pypost.core.metrics import MetricsManager

logger = logging.getLogger(__name__)

class MCPServerManager(QObject):
    status_changed = Signal(bool)  # True = running, False = stopped

    def __init__(self, metrics: MetricsManager | None = None):
        super().__init__()
        self._server_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._server_instance: Optional[uvicorn.Server] = None
        self._impl = MCPServerImpl(metrics=metrics)
        self._current_port = 1080
        self._current_host = "127.0.0.1"

    def start_server(self, port: int, tools: List[RequestData], host: str = "127.0.0.1"):
        if self.is_running():
            self.stop_server()

        self._current_port = port
        self._current_host = host
        self._impl.register_tools(tools)
        self._stop_event.clear()

        self._server_thread = threading.Thread(target=self._run_uvicorn, daemon=True)
        self._server_thread.start()
        logger.info("MCP server started on %s:%d", host, port)
        # Status emitted in thread is safer, or here if we trust it starts.
        # Let's emit here for UI responsiveness.
        self.status_changed.emit(True)

    def stop_server(self):
        if not self.is_running():
            return

        self._stop_event.set()
        if self._server_instance:
            self._server_instance.should_exit = True

        if self._server_thread:
            # Wait for thread to finish (with timeout to avoid freeze)
            self._server_thread.join(timeout=2.0)
            self._server_thread = None

        logger.info("MCP server stopped")
        self.status_changed.emit(False)

    def is_running(self) -> bool:
        return self._server_thread is not None and self._server_thread.is_alive()

    def update_tools(self, tools: List[RequestData]):
        if self.is_running():
            # Restart to refresh tools
            self.stop_server()
            self.start_server(self._current_port, tools, self._current_host)

    def _run_uvicorn(self):
        app = self._impl.create_app()
        # Ensure we run a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        config = uvicorn.Config(app=app, host=self._current_host, port=self._current_port, loop="asyncio")
        self._server_instance = uvicorn.Server(config)
        
        # Override install_signal_handlers because we are not in main thread
        self._server_instance.install_signal_handlers = lambda: None
        
        loop.run_until_complete(self._server_instance.serve())
