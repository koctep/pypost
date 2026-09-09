"""Automated failing repro tests for PYPOST-1082.

Verifies:
1. EnvPresenter has no mcp_status_text, mcp_tools_button_text, mcp_activity_button_text,
   or refresh_mcp_tools attribute.
2. EnvPresenter class docstring does not claim MCP lifecycle ownership.
3. EnvPresenter provides public mcp_controls property returning McpControlsPresenter.
4. MainWindow provides public mcp_controls property/attribute.
5. main_window_signals.wire_presenter_signals connects signals directly to
   window.mcp_controls.refresh_tools.
"""

from unittest.mock import MagicMock, patch

import pytest

from pypost.models.settings import AppSettings
from pypost.ui.main_window_signals import wire_presenter_signals
from pypost.ui.presenters.env_presenter import EnvPresenter
from pypost.ui.presenters.mcp_controls_presenter import McpControlsPresenter

pytestmark = pytest.mark.timeout(60)


class FakeStorage:
    def __init__(self, environments=None):
        self._environments = environments or []
        self.saved = []

    def load_environments(self):
        return list(self._environments)

    def save_environments(self, envs):
        self.saved.append(list(envs))


class FakeConfigManager:
    def __init__(self):
        self.saved = []

    def save_config(self, settings):
        self.saved.append(settings)


def _make_mcp_manager():
    mgr = MagicMock()
    mgr.status_changed = MagicMock()
    mgr.start_failed = MagicMock()
    mgr.activity_recorded = MagicMock()
    return mgr


@pytest.mark.usefixtures("qapp")
def test_env_presenter_has_no_retired_mcp_shims():
    """EnvPresenter must not define legacy MCP delegating shims."""
    assert not hasattr(EnvPresenter, "mcp_status_text"), (
        "EnvPresenter still has legacy shim 'mcp_status_text'"
    )
    assert not hasattr(EnvPresenter, "mcp_tools_button_text"), (
        "EnvPresenter still has legacy shim 'mcp_tools_button_text'"
    )
    assert not hasattr(EnvPresenter, "mcp_activity_button_text"), (
        "EnvPresenter still has legacy shim 'mcp_activity_button_text'"
    )
    assert not hasattr(EnvPresenter, "refresh_mcp_tools"), (
        "EnvPresenter still has legacy shim 'refresh_mcp_tools'"
    )


@pytest.mark.usefixtures("qapp")
def test_env_presenter_docstring_does_not_claim_mcp_lifecycle():
    """EnvPresenter class docstring must not claim MCP lifecycle ownership."""
    doc = EnvPresenter.__doc__ or ""
    assert "managing MCP lifecycle" not in doc, (
        f"EnvPresenter class docstring contains obsolete phrase 'managing MCP lifecycle': {doc!r}"
    )


@pytest.mark.usefixtures("qapp")
def test_env_presenter_provides_public_mcp_controls_property():
    """EnvPresenter must provide a public mcp_controls property returning McpControlsPresenter."""
    storage = FakeStorage()
    config = FakeConfigManager()
    mcp = _make_mcp_manager()
    settings = AppSettings()
    metrics = MagicMock()

    presenter = EnvPresenter(storage, config, mcp, settings, lambda: [], metrics)
    assert hasattr(presenter, "mcp_controls"), (
        "EnvPresenter must have a public 'mcp_controls' property"
    )
    assert isinstance(presenter.mcp_controls, McpControlsPresenter)
    assert presenter.mcp_controls is presenter._mcp_controls


def test_main_window_signals_connects_to_mcp_controls_refresh_tools():
    """wire_presenter_signals must connect mutation signals to window.mcp_controls.refresh_tools."""
    window = MagicMock()
    wire_presenter_signals(window)

    window.collections.collections_changed.connect.assert_any_call(
        window.mcp_controls.refresh_tools
    )
    window.collections.requests_deleted.connect.assert_any_call(
        window.mcp_controls.refresh_tools
    )
    window.tabs.request_saved.connect.assert_any_call(
        window.mcp_controls.refresh_tools
    )


@pytest.mark.usefixtures("qapp")
def test_main_window_provides_public_mcp_controls():
    """MainWindow must provide a public mcp_controls attribute delegating to env.mcp_controls."""
    with (
        patch("pypost.ui.main_window.StorageManager"),
        patch("pypost.ui.main_window.ConfigManager"),
        patch("pypost.ui.main_window.RequestManager"),
        patch("pypost.ui.main_window.StateManager") as mock_sm,
        patch("pypost.ui.mcp_server_controller.MCPServerManager"),
        patch("pypost.ui.main_window.CollectionsPresenter"),
        patch("pypost.ui.main_window.TabsPresenter"),
        patch("pypost.ui.main_window.HistoryPanel"),
        patch("pypost.ui.main_window.MainWindow._build_layout"),
        patch("pypost.ui.main_window.wire_presenter_signals"),
        patch("pypost.ui.main_window.MainWindow._create_menu_bar"),
        patch("pypost.ui.main_window.MainWindow._setup_shortcuts"),
        patch("pypost.ui.main_window.MainWindow.apply_settings"),
    ):
        mock_sm.return_value.settings = AppSettings()
        from pypost.ui.main_window import MainWindow

        window = MainWindow(
            metrics=MagicMock(),
            template_service=MagicMock(),
            config_manager=MagicMock(recovery_notice=None),
            settings=mock_sm.return_value.settings,
            state_manager=mock_sm.return_value,
            history_manager=MagicMock(),
            storage=MagicMock(),
            request_manager=MagicMock(),
            mcp_controller=MagicMock(),
            alert_manager_factory=MagicMock(),
        )

    assert hasattr(window, "mcp_controls"), "MainWindow must have public 'mcp_controls' attribute"
    assert window.mcp_controls is window.env.mcp_controls
