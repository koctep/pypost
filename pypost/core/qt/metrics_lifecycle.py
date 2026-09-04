from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from pypost.core.metrics_registry import MetricsRegistry
from pypost.core.metrics_server import MetricsServer


class MetricsLifecycle(QObject):
    _registry: MetricsRegistry

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

    def track_lifecycle_teardown(
        self,
        owner: str,
        outcome: str,
        elapsed_seconds: float,
        active_count: int,
        pending_count: int,
    ) -> None:
        self._registry.track_lifecycle_teardown(
            owner, outcome, elapsed_seconds, active_count, pending_count
        )

    def track_lifecycle_event(
        self, owner: str, event: str, count: int = 1
    ) -> None:
        self._registry.track_lifecycle_event(owner, event, count)

    def track_environment_update_disposition(self, disposition: str) -> None:
        self._registry.track_environment_update_disposition(disposition)

    def track_history_io_failure(self, operation: str) -> None:
        self._registry.track_history_io_failure(operation)
