"""PYPOST-870: caplog proof for agent_e2e_http_stub_installed (HTTP stub)."""

from __future__ import annotations

import logging

import pytest

from pypost.fixtures.agent_e2e_http import (
    CANNED_GOLDEN_OK,
    stub_agent_e2e_http,
)

pytestmark = pytest.mark.timeout(10)

_HTTP_LOGGER = "pypost.fixtures.agent_e2e_http"


def test_stub_agent_e2e_http_logs_installed_event(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """HTTP stub install emits agent_e2e_http_stub_installed name=golden_ok."""
    with caplog.at_level(logging.INFO, logger=_HTTP_LOGGER):
        with stub_agent_e2e_http(CANNED_GOLDEN_OK):
            pass
    assert "agent_e2e_http_stub_installed name=golden_ok" in caplog.text
