"""PYPOST-870 / PYPOST-903: caplog proof for agent_e2e_http_stub_installed."""

from __future__ import annotations

import logging
from typing import Any

import pytest

from pypost.fixtures.agent_e2e_http import (
    CANNED_DOUBLE_BODY_LOCK_OK,
    CANNED_GOLDEN_OK,
    CANNED_SEED_GET_OK,
    CANNED_SEED_POST_OK,
    GOLDEN_URL,
    make_canned_http_result,
    stub_agent_e2e_http,
)

pytestmark = pytest.mark.timeout(10)

_HTTP_LOGGER = "pypost.fixtures.agent_e2e_http"
_CUSTOM_SCENARIO_NAME = "scenario_alpha"
_CUSTOM_SCENARIO_RESULT = make_canned_http_result(
    url="https://example.test/scenario-alpha",
)

_InstallCase = tuple[Any, str, dict[str, Any]]

_INSTALL_MATRIX: list[_InstallCase] = [
    (CANNED_GOLDEN_OK, "golden_ok", {}),
    (CANNED_SEED_GET_OK, "seed_get_ok", {}),
    (CANNED_SEED_POST_OK, "seed_post_ok", {}),
    (CANNED_DOUBLE_BODY_LOCK_OK, "double_body_lock_ok", {}),
    ({GOLDEN_URL: CANNED_GOLDEN_OK}, "url_router", {}),
    (
        _CUSTOM_SCENARIO_RESULT,
        _CUSTOM_SCENARIO_NAME,
        {"name": _CUSTOM_SCENARIO_NAME},
    ),
]


@pytest.mark.parametrize(
    ("stub_arg", "expected_name", "stub_kwargs"),
    _INSTALL_MATRIX,
    ids=[case[1] for case in _INSTALL_MATRIX],
)
def test_stub_agent_e2e_http_logs_installed_event(
    caplog: pytest.LogCaptureFixture,
    stub_arg: Any,
    expected_name: str,
    stub_kwargs: dict[str, Any],
) -> None:
    """HTTP stub install emits agent_e2e_http_stub_installed name=<token>."""
    with caplog.at_level(logging.INFO, logger=_HTTP_LOGGER):
        with stub_agent_e2e_http(stub_arg, **stub_kwargs):
            pass
    assert f"agent_e2e_http_stub_installed name={expected_name}" in caplog.text
