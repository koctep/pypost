"""PYPOST-841: mid-start failure must clean temps and metrics."""

from __future__ import annotations

import socket
from typing import Any

import pytest
from PySide6.QtWidgets import QApplication

from pypost.agent.lifecycle import AgentAppSession

pytestmark = [
    pytest.mark.timeout(60),
    pytest.mark.agent_e2e,
]


def _port_is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def test_mid_start_non_timeout_failure_cleans_resources(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Non-TimeoutError during ready wait must still shut down partial session."""

    def _boom(*_args: Any, **_kwargs: Any) -> None:
        raise RuntimeError("forced mid-start ready failure")

    monkeypatch.setattr("pypost.agent.lifecycle.wait_until", _boom)

    session = AgentAppSession(offscreen=True, ready_timeout=30.0)
    with pytest.raises(RuntimeError, match="forced mid-start ready failure"):
        session.start()

    port = session._metrics_port
    assert port is not None
    assert session._composed is None
    assert session._temp_dirs == []
    assert _port_is_free(port), f"metrics port {port} still bound after failed start"


def test_mid_start_compose_failure_cleans_temp_dirs(
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """compose_app failure after temp allocation must release TemporaryDirectory."""

    def _boom(**_kwargs: Any) -> Any:
        raise RuntimeError("forced compose failure")

    monkeypatch.setattr("pypost.agent.lifecycle.compose_app", _boom)

    session = AgentAppSession(offscreen=True, ready_timeout=30.0)
    with pytest.raises(RuntimeError, match="forced compose failure"):
        session.start()

    assert session._composed is None
    assert session._temp_dirs == []
