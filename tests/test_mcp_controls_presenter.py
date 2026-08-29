from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QWidget

from pypost.core.mcp_activity_log import McpActivityEntry
from pypost.models.models import Environment
from pypost.models.settings import AppSettings, McpServerConfiguration
from pypost.ui.presenters.mcp_controls_presenter import (
    McpControlsPresenter,
    McpServerController,
)

pytestmark = pytest.mark.timeout(30)


def test_mcp_controls_presenter_widgets_and_initial_state(qapp):
    parent = QWidget()
    manager = MagicMock()
    settings = AppSettings(mcp_host="127.0.0.1", mcp_port=9080)
    metrics = MagicMock()

    presenter = McpControlsPresenter(
        mcp_manager=manager,
        settings_provider=lambda: settings,
        get_collections=lambda: [],
        get_environments=lambda: [],
        current_environment=lambda: None,
        metrics=metrics,
        dialog_parent=parent,
    )

    assert len(presenter.widgets) == 4
    assert presenter.status_text() == "MCP: OFF"
    assert presenter.tools_button_text() == "MCP Tools (0)"
    assert presenter.activity_button_text() == "MCP Activity (0)"


def test_open_mcp_servers_without_controller_logs_warning(qapp, caplog):
    parent = QWidget()
    manager = MagicMock()
    settings = AppSettings()
    metrics = MagicMock()

    presenter = McpControlsPresenter(
        mcp_manager=manager,
        settings_provider=lambda: settings,
        get_collections=lambda: [],
        get_environments=lambda: [],
        current_environment=lambda: None,
        metrics=metrics,
        dialog_parent=parent,
    )

    with caplog.at_level(logging.WARNING):
        presenter._open_mcp_servers()

    assert "mcp_servers_dialog_no_controller" in caplog.text


def test_open_mcp_servers_with_controller_logs_info_and_constructs_dialog(qapp, caplog):
    parent = QWidget()
    manager = MagicMock()
    settings = AppSettings(mcp_host="127.0.0.1", mcp_port=9080)
    metrics = MagicMock()
    env = Environment(id="env-1", name="Env 1", enable_mcp=True)

    controller = MagicMock(spec=McpServerController)
    configs = [
        McpServerConfiguration(
            id="srv-1",
            name="Server 1",
            port=9080,
            collection_id="col-1",
            environment_id="env-1",
        ),
        McpServerConfiguration(
            id="srv-2",
            name="Server 2",
            port=9081,
            collection_id="col-2",
            environment_id="env-2",
        ),
    ]
    controller.mcp_server_configurations.return_value = configs
    controller.mcp_server_count.return_value = 2

    presenter = McpControlsPresenter(
        mcp_manager=manager,
        settings_provider=lambda: settings,
        get_collections=lambda: [],
        get_environments=lambda: [env],
        current_environment=lambda: env,
        metrics=metrics,
        dialog_parent=parent,
    )
    presenter.set_server_controller(controller)

    with patch(
        "pypost.ui.presenters.mcp_controls_presenter.McpServersDialog"
    ) as mock_dialog_cls:
        mock_dialog_instance = MagicMock()
        mock_dialog_cls.return_value = mock_dialog_instance

        with caplog.at_level(logging.INFO):
            presenter._open_mcp_servers()

        assert "mcp_servers_dialog_opened server_count=2" in caplog.text
        controller.mcp_server_count.assert_called_once()
        controller.mcp_server_configurations.assert_not_called()

        mock_dialog_cls.assert_called_once()
        _, kwargs = mock_dialog_cls.call_args

        # Verify all 13 injected callables/dependencies
        assert kwargs["configurations"] == controller.mcp_server_configurations
        assert kwargs["status_for"] == controller.mcp_server_status
        assert kwargs["save"] == controller.upsert_mcp_server
        assert kwargs["remove"] == controller.remove_mcp_server
        assert kwargs["start"] == controller.start_mcp_server
        assert kwargs["stop"] == controller.stop_mcp_server
        assert kwargs["activity"] == controller.mcp_server_activity
        assert callable(kwargs["collections"])
        assert callable(kwargs["environments"])
        assert callable(kwargs["legacy_environment"])
        assert kwargs["legacy_host"] == "127.0.0.1"
        assert kwargs["legacy_port"] == 9080
        assert kwargs["parent"] == parent

        mock_dialog_instance.exec.assert_called_once()


def test_selected_legacy_mcp_environment(qapp):
    parent = QWidget()
    manager = MagicMock()
    settings = AppSettings()
    metrics = MagicMock()

    current_env = None

    presenter = McpControlsPresenter(
        mcp_manager=manager,
        settings_provider=lambda: settings,
        get_collections=lambda: [],
        get_environments=lambda: [],
        current_environment=lambda: current_env,
        metrics=metrics,
        dialog_parent=parent,
    )

    assert presenter._selected_legacy_mcp_environment() is None

    current_env = Environment(id="env-off", name="Off", enable_mcp=False)
    assert presenter._selected_legacy_mcp_environment() is None

    current_env = Environment(id="env-on", name="On", enable_mcp=True)
    assert presenter._selected_legacy_mcp_environment() == current_env


def test_open_mcp_activity_dialog_and_recording_lifecycle(qapp):
    parent = QWidget()
    manager = MagicMock()
    entry = McpActivityEntry.new_list_tools(tool_count=1)
    manager.activity_log.get_entries.return_value = [entry]
    manager.activity_log.count.return_value = 1
    settings = AppSettings()
    metrics = MagicMock()

    presenter = McpControlsPresenter(
        mcp_manager=manager,
        settings_provider=lambda: settings,
        get_collections=lambda: [],
        get_environments=lambda: [],
        current_environment=lambda: None,
        metrics=metrics,
        dialog_parent=parent,
    )

    with patch(
        "pypost.ui.presenters.mcp_controls_presenter.McpActivityDialog"
    ) as mock_dialog_cls:
        mock_dialog_instance = MagicMock()
        mock_dialog_cls.return_value = mock_dialog_instance

        presenter._open_mcp_activity()
        mock_dialog_cls.assert_called_once_with([entry], parent)
        mock_dialog_instance.exec.assert_called_once()

        # Activity recording updates badge and open dialog
        presenter._on_mcp_activity_recorded(object())
        assert presenter.activity_button_text() == "MCP Activity (1)"
        mock_dialog_instance.set_entries.assert_called_once()

        presenter._on_mcp_activity_dialog_closed()
        assert presenter._mcp_activity_dialog is None


def test_mcp_status_changed_and_start_failed_ui(qapp, caplog):
    parent = QWidget()
    manager = MagicMock()
    settings = AppSettings(mcp_host="127.0.0.1", mcp_port=9080)
    metrics = MagicMock()

    presenter = McpControlsPresenter(
        mcp_manager=manager,
        settings_provider=lambda: settings,
        get_collections=lambda: [],
        get_environments=lambda: [],
        current_environment=lambda: None,
        metrics=metrics,
        dialog_parent=parent,
    )

    with caplog.at_level(logging.INFO):
        presenter._on_mcp_status_changed(True)
    assert presenter.status_text() == "MCP: ON (127.0.0.1:9080)"
    assert "mcp_server_started host=127.0.0.1 port=9080" in caplog.text

    presenter._on_mcp_status_changed(False)
    assert presenter.status_text() == "MCP: OFF"
    assert "mcp_server_stopped" in caplog.text

    with patch(
        "pypost.ui.presenters.mcp_controls_presenter.show_mcp_server_start_failed"
    ) as mock_show:
        presenter._on_mcp_start_failed("Port in use")
        assert presenter.status_text() == "MCP: OFF"
        mock_show.assert_called_once_with(parent, "Port in use")


def test_handle_environment_selected_starts_and_stops_legacy_server(qapp):
    parent = QWidget()
    manager = MagicMock()
    manager.is_running.return_value = False
    settings = AppSettings(mcp_host="127.0.0.1", mcp_port=9080)
    metrics = MagicMock()
    env_mcp = Environment(id="env-mcp", name="MCP Env", enable_mcp=True)

    presenter = McpControlsPresenter(
        mcp_manager=manager,
        settings_provider=lambda: settings,
        get_collections=lambda: [],
        get_environments=lambda: [env_mcp],
        current_environment=lambda: env_mcp,
        metrics=metrics,
        dialog_parent=parent,
    )

    presenter.handle_environment_selected(env_mcp)
    manager.start_server.assert_called_once_with(
        port=9080,
        tools=[],
        host="127.0.0.1",
    )
    assert presenter._active_environment == env_mcp

    # Deselecting stops server
    manager.is_running.return_value = True
    presenter.handle_environment_selected(None)
    manager.stop_server.assert_called_once()
    assert presenter._active_environment is None
    metrics.track_mcp_active_env_changed.assert_called_once()


def test_on_environment_manager_closed_reconciles_and_refreshes(qapp):
    parent = QWidget()
    manager = MagicMock()
    registry = MagicMock()
    settings = AppSettings()
    metrics = MagicMock()
    env1 = Environment(id="e1", name="Env 1")
    env2 = Environment(id="e2", name="Env 2")

    presenter = McpControlsPresenter(
        mcp_manager=manager,
        settings_provider=lambda: settings,
        get_collections=lambda: [],
        get_environments=lambda: [env1, env2],
        current_environment=lambda: None,
        metrics=metrics,
        dialog_parent=parent,
        mcp_registry=registry,
    )

    presenter.on_environment_manager_closed()
    registry.reconcile_references.assert_called_once()
    registry.refresh_environment.assert_any_call("e1")
    registry.refresh_environment.assert_any_call("e2")
