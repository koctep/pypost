from __future__ import annotations

from PySide6.QtCore import Signal

from pypost.core.metrics_registry import MetricsRegistry
from pypost.core.metrics_server import MetricsServer
from pypost.core.qt.metrics_autocomplete import MetricsAutocompleteMixin
from pypost.core.qt.metrics_lifecycle import MetricsLifecycle
from pypost.core.qt.metrics_tracking import MetricsTrackingMixin
from pypost.core.qt.metrics_websocket import MetricsWebSocketMixin


# Qt-facing listener lifecycle is inherited from MetricsLifecycle.
class MetricsManager(
    MetricsLifecycle,
    MetricsAutocompleteMixin,
    MetricsTrackingMixin,
    MetricsWebSocketMixin,
):
    start_failed = Signal(str)  # operator-facing bind / startup error

    def __init__(self) -> None:
        super().__init__()
        self._registry = MetricsRegistry()
        self._server = MetricsServer(self._registry)
        self._pending_start_failure: str | None = None
        self._start_failed_connected = False
        self._server.set_start_failed_handler(self._handle_start_failed)
        self._bind_metrics_server(self._server)

    def _handle_start_failed(self, message: str) -> None:
        if self._start_failed_connected:
            self.start_failed.emit(message)
            return
        self._pending_start_failure = message

    def connect_start_failed(self, slot) -> None:
        """Connect UI slot and replay a failure that occurred before connect."""
        self.start_failed.connect(slot)
        self._start_failed_connected = True
        pending = self._pending_start_failure
        if pending is not None:
            self._pending_start_failure = None
            slot(pending)

    @property
    def registry(self):
        return self._registry.registry

    def start_server(self, host: str, port: int) -> None:
        self._server.start_server(host, port)

    def stop_server(self) -> None:
        self._server.stop_server()

    def restart_server(self, host: str, port: int) -> None:
        self._server.restart_server(host, port)

    async def list_resources(self):
        return await self._server.list_resources()

    async def read_resource(self, uri: str):
        return await self._server.read_resource(uri)
