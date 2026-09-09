"""Qt bindings for the framework-neutral WebSocket MCP probe orchestration."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QCoreApplication

from pypost.core.qt.websocket_probe_runner import WebSocketProbeRunner
from pypost.core.websocket_mcp_tools import execute_websocket_probe


def execute_qt_websocket_probe(*args: Any, **kwargs: Any):
    """Execute a probe with Qt thread and event-pump dependencies injected."""
    return execute_websocket_probe(
        *args,
        **kwargs,
        runner_factory=WebSocketProbeRunner,
        process_events=QCoreApplication.processEvents,
    )
