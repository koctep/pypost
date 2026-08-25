from __future__ import annotations

from pypost.core.metrics_registry import MetricsRegistry


class MetricsWebSocketMixin:
    """Explicit delegation for WebSocket metrics (PYPOST-1146)."""

    _registry: MetricsRegistry

    def track_websocket_session_opened(self, outcome: str) -> None:
        self._registry.track_websocket_session_opened(outcome)

    def track_websocket_session_closed(self, reason: str) -> None:
        self._registry.track_websocket_session_closed(reason)

    def track_websocket_message(self, direction: str, kind: str) -> None:
        self._registry.track_websocket_message(direction, kind)

    def track_websocket_message_bytes(self, direction: str, byte_count: int) -> None:
        self._registry.track_websocket_message_bytes(direction, byte_count)

    def track_websocket_stream_entries_dropped(
        self, reason: str, count: int = 1
    ) -> None:
        self._registry.track_websocket_stream_entries_dropped(reason, count)

    def track_websocket_reconnect_attempt(self, outcome: str) -> None:
        self._registry.track_websocket_reconnect_attempt(outcome)

    def set_websocket_active_sessions(self, count: int) -> None:
        self._registry.set_websocket_active_sessions(count)

    def track_websocket_session_start_refused(self, reason: str) -> None:
        self._registry.track_websocket_session_start_refused(reason)

    def track_websocket_probe_duration(
        self, outcome: str, duration_seconds: float
    ) -> None:
        self._registry.track_websocket_probe_duration(outcome, duration_seconds)
