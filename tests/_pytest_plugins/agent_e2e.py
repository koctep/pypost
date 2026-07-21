"""Pytest fixtures for agent e2e session packaging (PYPOST-858)."""

from __future__ import annotations

import logging
from typing import Iterator

import pytest

from pypost.agent.lifecycle import AgentAppSession
from tests.helpers.agent_e2e_seed import seeded_agent_dirs

logger = logging.getLogger(__name__)


@pytest.fixture
def agent_e2e_session() -> Iterator[AgentAppSession]:
    """Yield a ready blank AgentAppSession (function-scoped, offscreen)."""
    with AgentAppSession(offscreen=True, ready_timeout=30.0) as session:
        logger.info("agent_e2e_fixture_ready mode=blank")
        yield session


@pytest.fixture
def seeded_agent_e2e_session() -> Iterator[AgentAppSession]:
    """Yield a ready AgentAppSession with PYPOST-857 seed written first."""
    with seeded_agent_dirs() as (config_dir, data_dir):
        with AgentAppSession(
            offscreen=True,
            config_dir=config_dir,
            data_dir=data_dir,
            ready_timeout=30.0,
        ) as session:
            logger.info("agent_e2e_fixture_ready mode=seeded")
            yield session
