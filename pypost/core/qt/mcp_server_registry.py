"""Qt signal adapter for the framework-neutral MCP registry."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QObject, Signal

from pypost.core.mcp_server_registry import (
    MCPServerRegistry,
    McpServerRuntimeFactory,
    ServerState,
)
from pypost.core.metrics_protocol import MetricsTrackerProtocol
from pypost.models.models import Collection, Environment


class QtMCPServerRegistry(QObject, MCPServerRegistry):
    """Expose registry notifications as queued-capable Qt signals.

    Runtime callbacks may arrive on uvicorn watcher threads.  Emitting a Qt
    signal is thread-safe; Qt marshals connected QObject slots according to
    their thread affinity, while the core registry protects its own state.
    """

    status_changed = Signal(str, str, str)
    reconfiguration_finished = Signal(str, bool)

    def __init__(
        self,
        *,
        collection_lookup: Callable[[str], Collection | None] | None = None,
        environment_lookup: Callable[[str], Environment | None] | None = None,
        metrics: MetricsTrackerProtocol | None = None,
        runtime_factory: McpServerRuntimeFactory | None = None,
    ) -> None:
        QObject.__init__(self)
        MCPServerRegistry.__init__(
            self,
            collection_lookup=collection_lookup,
            environment_lookup=environment_lookup,
            metrics=metrics,
            runtime_factory=runtime_factory,
        )
        self.connect_status_changed(self._emit_status_changed)
        self.connect_reconfiguration_finished(self.reconfiguration_finished.emit)

    def _emit_status_changed(
        self, instance_id: str, state: ServerState, message: str
    ) -> None:
        self.status_changed.emit(instance_id, state, message)
