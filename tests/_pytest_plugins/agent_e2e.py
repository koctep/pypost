"""Pytest fixtures for agent e2e session + HTTP packaging (858/859)."""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterator
from typing import Any

import pytest

from pypost.agent.lifecycle import AgentAppSession
from pypost.fixtures.agent_e2e_http import stub_agent_e2e_http
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


@pytest.fixture
def agent_e2e_http_stub() -> Callable[..., Any]:
    """Yield ``stub_agent_e2e_http`` for ``with agent_e2e_http_stub(...):``."""
    return stub_agent_e2e_http
