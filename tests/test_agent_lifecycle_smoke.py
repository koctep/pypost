"""PYPOST-833: smoke — agent launch → ready → shutdown."""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from pypost.agent.lifecycle import AgentAppSession

pytestmark = pytest.mark.timeout(60)


def test_agent_app_session_launch_ready_shutdown(qapp: QApplication) -> None:
    """FR7: launch → is_ui_ready → clean shutdown under offscreen Qt."""
    assert QApplication.instance() is qapp

    with AgentAppSession(offscreen=True, ready_timeout=30.0) as session:
        assert session.window.is_ui_ready is True
        assert session.app is qapp

    with pytest.raises(RuntimeError, match="has not been started"):
        _ = session.window


def test_agent_app_session_relaunch_after_shutdown(qapp: QApplication) -> None:
    """FR6: a subsequent launch succeeds after clean shutdown."""
    with AgentAppSession(offscreen=True, ready_timeout=30.0) as first:
        assert first.window.is_ui_ready is True

    with AgentAppSession(offscreen=True, ready_timeout=30.0) as second:
        assert second.window.is_ui_ready is True
