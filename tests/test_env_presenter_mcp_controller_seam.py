"""Failing repro tests for PYPOST-1107: retiring EnvPresenter.set_mcp_server_controller."""

import pytest
from pypost.ui.presenters.env_presenter import EnvPresenter

pytestmark = pytest.mark.timeout(30)


def test_env_presenter_does_not_have_set_mcp_server_controller() -> None:
    """EnvPresenter should not expose legacy passthrough set_mcp_server_controller."""
    assert not hasattr(EnvPresenter, "set_mcp_server_controller"), (
        "EnvPresenter still exposes legacy set_mcp_server_controller shim"
    )
