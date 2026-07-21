"""PYPOST-833: smoke — agent launch → ready → shutdown."""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from pypost.agent.lifecycle import AgentAppSession

pytestmark = [
    pytest.mark.timeout(60),
    pytest.mark.agent_e2e,
]


def test_agent_app_session_launch_ready_shutdown(
    qapp: QApplication,
    agent_e2e_session: AgentAppSession,
) -> None:
    """FR7: launch → is_ui_ready under offscreen Qt (shared fixture)."""
    assert QApplication.instance() is qapp
    session = agent_e2e_session
    assert session.window.is_ui_ready is True
    assert session.app is qapp


def test_agent_app_session_window_unavailable_after_shutdown() -> None:
    """After context exit, session.window raises (direct lifecycle API)."""
    with AgentAppSession(offscreen=True, ready_timeout=30.0) as session:
        assert session.window.is_ui_ready is True

    with pytest.raises(RuntimeError, match="has not been started"):
        _ = session.window


def test_agent_app_session_relaunch_after_shutdown(qapp: QApplication) -> None:
    """FR6: a subsequent launch succeeds after clean shutdown."""
    with AgentAppSession(offscreen=True, ready_timeout=30.0) as first:
        assert first.window.is_ui_ready is True

    with AgentAppSession(offscreen=True, ready_timeout=30.0) as second:
        assert second.window.is_ui_ready is True
