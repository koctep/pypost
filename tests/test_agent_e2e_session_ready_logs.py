"""PYPOST-899: live-session caplog smoke for agent_e2e_fixture_ready."""

from __future__ import annotations

import logging

import pytest
from PySide6.QtWidgets import QApplication

from pypost.agent.lifecycle import AgentAppSession

pytestmark = [
    pytest.mark.timeout(60),
    pytest.mark.agent_e2e,
]

_PACKAGING_LOGGER = "tests._pytest_plugins.agent_e2e"


def test_live_agent_e2e_session_logs_fixture_ready_blank(
    caplog: pytest.LogCaptureFixture,
    request: pytest.FixtureRequest,
    qapp: QApplication,
) -> None:
    """Live blank fixture emits agent_e2e_fixture_ready mode=blank (no mocks)."""
    assert QApplication.instance() is qapp
    with caplog.at_level(logging.INFO, logger=_PACKAGING_LOGGER):
        session = request.getfixturevalue("agent_e2e_session")
    assert isinstance(session, AgentAppSession)
    assert session.window.is_ui_ready is True
    assert "agent_e2e_fixture_ready mode=blank" in caplog.text


def test_live_seeded_agent_e2e_session_logs_fixture_ready_seeded(
    caplog: pytest.LogCaptureFixture,
    request: pytest.FixtureRequest,
    qapp: QApplication,
) -> None:
    """Live seeded fixture emits agent_e2e_fixture_ready mode=seeded (no mocks)."""
    assert QApplication.instance() is qapp
    with caplog.at_level(logging.INFO, logger=_PACKAGING_LOGGER):
        session = request.getfixturevalue("seeded_agent_e2e_session")
    assert isinstance(session, AgentAppSession)
    assert session.window.is_ui_ready is True
    assert "agent_e2e_fixture_ready mode=seeded" in caplog.text
