"""Pytest fixtures for agent e2e session + HTTP packaging (858/860/875)."""

from __future__ import annotations

import logging
from collections.abc import Callable, Generator, Iterator
from pathlib import Path
from typing import Any

import pytest

from pypost.agent.lifecycle import (
    AgentAppSession,
    set_agent_session_failure_dump_hook,
)
from pypost.fixtures.agent_e2e_failure import (
    clear_failure_dump_context,
    dump_agent_e2e_failure_artifacts,
    make_direct_session_failure_dump_hook,
    resolve_artifact_root,
    session_from_funcargs,
    set_failure_dump_context,
)
from pypost.fixtures.agent_e2e_http import stub_agent_e2e_http
from tests.helpers.agent_e2e_seed import seeded_agent_dirs

logger = logging.getLogger(__name__)

# Install once when the packaging plugin loads (covers direct constructions).
set_agent_session_failure_dump_hook(make_direct_session_failure_dump_hook())


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


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item: pytest.Item) -> None:
    """Bind nodeid / artifact root for direct ``AgentAppSession`` dumps."""
    rootpath = getattr(item.config, "rootpath", None) or item.config.rootdir
    set_failure_dump_context(
        nodeid=item.nodeid,
        artifact_root=resolve_artifact_root(Path(str(rootpath))),
    )


@pytest.hookimpl(trylast=True)
def pytest_runtest_teardown(item: pytest.Item, nextitem: pytest.Item | None) -> None:
    """Clear per-test dump context after the item finishes."""
    del item, nextitem
    clear_failure_dump_context()


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(
    item: pytest.Item,
    call: pytest.CallInfo[None],
) -> Generator[None, None, None]:
    """Dump masked UI snapshot + diagnostics on agent e2e call failure."""
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or not report.failed:
        return
    resolved = session_from_funcargs(getattr(item, "funcargs", {}) or {})
    if resolved is None:
        return
    session, fixture_name = resolved
    exc_type: str | None = None
    exc_message: str | None = None
    if call.excinfo is not None:
        exc_type = call.excinfo.typename
        exc_message = str(call.excinfo.value)
    rootpath = getattr(item.config, "rootpath", None) or item.config.rootdir
    dump_agent_e2e_failure_artifacts(
        session,
        nodeid=item.nodeid,
        exc_type=exc_type,
        exc_message=exc_message,
        session_source=fixture_name,
        artifact_root=resolve_artifact_root(Path(str(rootpath))),
    )
