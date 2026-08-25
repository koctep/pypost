"""PYPOST-1146: MetricsManager must expose explicit delegation, not __getattr__."""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from prometheus_client import generate_latest

from pypost.core.qt.metrics import MetricsManager

pytestmark = pytest.mark.timeout(10)


def _method_defined_in_mro(cls: type, method_name: str) -> bool:
    for base in cls.__mro__:
        if base is object:
            break
        if method_name in base.__dict__:
            return True
    return False

_WEBSOCKET_METHODS = (
    "track_websocket_session_opened",
    "track_websocket_session_closed",
    "track_websocket_message",
    "track_websocket_message_bytes",
    "track_websocket_stream_entries_dropped",
    "track_websocket_reconnect_attempt",
    "set_websocket_active_sessions",
    "track_websocket_session_start_refused",
    "track_websocket_probe_duration",
)


def test_metrics_manager_has_no_dynamic_getattr_delegation() -> None:
    assert "__getattr__" not in MetricsManager.__dict__


@pytest.mark.parametrize("method_name", _WEBSOCKET_METHODS)
def test_metrics_manager_defines_explicit_websocket_methods(method_name: str) -> None:
    assert _method_defined_in_mro(MetricsManager, method_name)


def test_metrics_manager_websocket_methods_delegate_to_registry(
    qapp: QApplication,
) -> None:
    manager = MetricsManager()
    manager.track_websocket_session_opened(outcome="success")
    manager.set_websocket_active_sessions(1)

    scrape = generate_latest(manager.registry).decode("utf-8")
    assert 'websocket_sessions_opened_total{outcome="success"} 1.0' in scrape
    assert "websocket_active_sessions 1.0" in scrape
