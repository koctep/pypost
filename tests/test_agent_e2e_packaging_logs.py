"""PYPOST-867: caplog proof for agent_e2e_fixture_ready (packaging)."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from tests._pytest_plugins import agent_e2e as packaging

pytestmark = pytest.mark.timeout(30)

_PACKAGING_LOGGER = "tests._pytest_plugins.agent_e2e"


def _fixture_fn(fixture: Any) -> Any:
    """Return the underlying generator function for a pytest fixture."""
    return fixture._get_wrapped_function()


def _run_fixture(gen: Iterator[Any]) -> Any:
    """Drive a yield-fixture generator through setup and teardown."""
    value = next(gen)
    with pytest.raises(StopIteration):
        next(gen)
    return value


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
            session = _run_fixture(_fixture_fn(packaging.agent_e2e_session)())
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
                session = _run_fixture(
                    _fixture_fn(packaging.seeded_agent_e2e_session)(),
                )
    assert session is cm.__enter__.return_value
    assert "agent_e2e_fixture_ready mode=seeded" in caplog.text
