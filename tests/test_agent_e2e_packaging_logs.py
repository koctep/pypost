"""PYPOST-867: caplog proof for agent_e2e_fixture_ready (packaging)."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tests._pytest_plugins import agent_e2e as packaging
from tests.helpers.fixture_drive import call_yield_fixture

pytestmark = pytest.mark.timeout(30)

_PACKAGING_LOGGER = "tests._pytest_plugins.agent_e2e"


@contextmanager
def _fake_seeded_dirs() -> Iterator[tuple[Path, Path]]:
    yield (Path("/tmp/pypost-e2e-config"), Path("/tmp/pypost-e2e-data"))


def _mock_agent_session_cm() -> MagicMock:
    session = MagicMock(name="AgentAppSession")
    cm = MagicMock()
    cm.__enter__.return_value = session
    cm.__exit__.return_value = False
    return cm


def test_agent_e2e_session_logs_fixture_ready_blank(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Blank packaging fixture emits agent_e2e_fixture_ready mode=blank."""
    cm = _mock_agent_session_cm()
    with patch.object(packaging, "AgentAppSession", return_value=cm):
        with caplog.at_level(logging.INFO, logger=_PACKAGING_LOGGER):
            session = call_yield_fixture(packaging.agent_e2e_session)
    assert session is cm.__enter__.return_value
    assert "agent_e2e_fixture_ready mode=blank" in caplog.text


def test_seeded_agent_e2e_session_logs_fixture_ready_seeded(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Seeded packaging fixture emits agent_e2e_fixture_ready mode=seeded."""
    cm = _mock_agent_session_cm()
    with patch.object(packaging, "AgentAppSession", return_value=cm):
        with patch.object(packaging, "seeded_agent_dirs", _fake_seeded_dirs):
            with caplog.at_level(logging.INFO, logger=_PACKAGING_LOGGER):
                session = call_yield_fixture(packaging.seeded_agent_e2e_session)
    assert session is cm.__enter__.return_value
    assert "agent_e2e_fixture_ready mode=seeded" in caplog.text
