from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from pypost.core.metrics_server import MetricsServer


class MetricsLifecycle(QObject):
    listening_changed = Signal(bool)
    unexpected_exit = Signal(str)

    def _bind_metrics_server(self, server: MetricsServer) -> None:
        self._lifecycle_server = server
        server.set_lifecycle_handlers(
            listening_changed=self.listening_changed.emit,
            unexpected_exit=self.unexpected_exit.emit,
        )

    @property
    def is_listening(self) -> bool:
        return self._lifecycle_server.is_listening
