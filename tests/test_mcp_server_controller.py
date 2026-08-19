from __future__ import annotations

import logging
from unittest.mock import MagicMock

import pytest

from pypost.core.mcp_activity_log import McpActivityEntry
from pypost.core.mcp_server_registry import MCPServerRegistry, McpServerStatus
from pypost.models.models import Collection
from pypost.models.settings import AppSettings, McpServerConfiguration
from pypost.ui.mcp_server_controller import McpServerSettingsController

pytestmark = pytest.mark.timeout(30)


def _make_config(
    instance_id: str = "srv-1",
    name: str = "Test Server",
    collection_id: str = "col-1",
    environment_id: str = "env-1",
    host: str = "127.0.0.1",
    port: int = 9080,
    enabled: bool = False,
) -> McpServerConfiguration:
    return McpServerConfiguration(
        id=instance_id,
        name=name,
        collection_id=collection_id,
        environment_id=environment_id,
        host=host,
        port=port,
        enabled=enabled,
    )


class FakeConfigManager:
    def __init__(self) -> None:
        self.saved: list[AppSettings] = []

    def save_config(self, settings: AppSettings) -> None:
        self.saved.append(settings)


def test_mcp_server_controller_configurations_returns_deep_copies():
    config = _make_config("srv-1", "Original")
    settings = AppSettings(mcp_servers=[config])
    config_manager = FakeConfigManager()
    registry = MagicMock(spec=MCPServerRegistry)

    controller = McpServerSettingsController(
        settings_provider=lambda: settings,
        config_manager=config_manager,
        collections_provider=lambda: None,
        get_collections=lambda: [],
        environment_lookup=lambda _id: None,
        metrics=MagicMock(),
        template_service=MagicMock(),
        mcp_manager=MagicMock(),
        registry=registry,
    )

    configs = controller.mcp_server_configurations()
    assert len(configs) == 1
    assert configs[0].name == "Original"

    configs[0].name = "Mutated"
    fresh = controller.mcp_server_configurations()
    assert fresh[0].name == "Original"


def test_mcp_server_controller_status_delegates_to_registry():
    settings = AppSettings()
    config_manager = FakeConfigManager()
    registry = MagicMock(spec=MCPServerRegistry)
    expected_status = McpServerStatus(id="srv-1", state="running")
    registry.status.return_value = expected_status

    controller = McpServerSettingsController(
        settings_provider=lambda: settings,
        config_manager=config_manager,
        collections_provider=lambda: None,
        get_collections=lambda: [],
        environment_lookup=lambda _id: None,
        metrics=MagicMock(),
        template_service=MagicMock(),
        mcp_manager=MagicMock(),
        registry=registry,
    )

    status = controller.mcp_server_status("srv-1")
    assert status == expected_status
    registry.status.assert_called_once_with("srv-1")


def test_mcp_server_activity_returns_entries_when_manager_found():
    settings = AppSettings()
    config_manager = FakeConfigManager()
    registry = MagicMock(spec=MCPServerRegistry)
    manager = MagicMock()
    entry = McpActivityEntry.new_list_tools(tool_count=3)
    manager.activity_log.get_entries.return_value = [entry]
    registry.manager_for.return_value = manager

    controller = McpServerSettingsController(
        settings_provider=lambda: settings,
        config_manager=config_manager,
        collections_provider=lambda: None,
        get_collections=lambda: [],
        environment_lookup=lambda _id: None,
        metrics=MagicMock(),
        template_service=MagicMock(),
        mcp_manager=MagicMock(),
        registry=registry,
    )

    entries = controller.mcp_server_activity("srv-1")
    assert entries == [entry]
    registry.manager_for.assert_called_once_with("srv-1")


def test_mcp_server_activity_handles_keyerror_with_debug_log(caplog):
    settings = AppSettings()
    config_manager = FakeConfigManager()
    registry = MagicMock(spec=MCPServerRegistry)
    registry.manager_for.side_effect = KeyError("silent-srv")

    controller = McpServerSettingsController(
        settings_provider=lambda: settings,
        config_manager=config_manager,
        collections_provider=lambda: None,
        get_collections=lambda: [],
        environment_lookup=lambda _id: None,
        metrics=MagicMock(),
        template_service=MagicMock(),
        mcp_manager=MagicMock(),
        registry=registry,
    )

    with caplog.at_level(logging.DEBUG):
        entries = controller.mcp_server_activity("silent-srv")

    assert entries == []
    assert "mcp_server_activity_unavailable instance_id=silent-srv" in caplog.text


def test_upsert_mcp_server_creates_and_persists_new_configuration(caplog):
    settings = AppSettings(mcp_servers=[])
    config_manager = FakeConfigManager()
    registry = MagicMock(spec=MCPServerRegistry)
    new_config = _make_config("srv-new", "Brand New")

    controller = McpServerSettingsController(
        settings_provider=lambda: settings,
        config_manager=config_manager,
        collections_provider=lambda: None,
        get_collections=lambda: [],
        environment_lookup=lambda _id: None,
        metrics=MagicMock(),
        template_service=MagicMock(),
        mcp_manager=MagicMock(),
        registry=registry,
    )

    with caplog.at_level(logging.INFO):
        controller.upsert_mcp_server(new_config)

    registry.upsert.assert_called_with(new_config)
    assert len(settings.mcp_servers) == 1
    assert settings.mcp_servers[0].id == "srv-new"
    assert len(config_manager.saved) == 1
    assert "mcp_servers_persist_requested reason=create count=1" in caplog.text


def test_upsert_mcp_server_updates_existing_stopped_configuration(caplog):
    initial = _make_config("srv-1", "Initial Name")
    settings = AppSettings(mcp_servers=[initial])
    config_manager = FakeConfigManager()
    registry = MagicMock(spec=MCPServerRegistry)
    registry.is_running.return_value = False

    controller = McpServerSettingsController(
        settings_provider=lambda: settings,
        config_manager=config_manager,
        collections_provider=lambda: None,
        get_collections=lambda: [],
        environment_lookup=lambda _id: None,
        metrics=MagicMock(),
        template_service=MagicMock(),
        mcp_manager=MagicMock(),
        registry=registry,
    )

    updated = _make_config("srv-1", "Updated Name")
    with caplog.at_level(logging.INFO):
        controller.upsert_mcp_server(updated)

    registry.upsert.assert_called_with(updated)
    assert len(settings.mcp_servers) == 1
    assert settings.mcp_servers[0].name == "Updated Name"
    assert "mcp_servers_persist_requested reason=update count=1" in caplog.text


def test_upsert_mcp_server_reconfigures_running_server_without_settings_mutation():
    initial = _make_config("srv-1", "Running Initial", enabled=True)
    settings = AppSettings(mcp_servers=[initial])
    config_manager = FakeConfigManager()
    registry = MagicMock(spec=MCPServerRegistry)
    registry.is_running.return_value = True

    controller = McpServerSettingsController(
        settings_provider=lambda: settings,
        config_manager=config_manager,
        collections_provider=lambda: None,
        get_collections=lambda: [],
        environment_lookup=lambda _id: None,
        metrics=MagicMock(),
        template_service=MagicMock(),
        mcp_manager=MagicMock(),
        registry=registry,
    )

    edited = _make_config("srv-1", "Running Edited", enabled=True)
    controller.upsert_mcp_server(edited)

    registry.reconfigure.assert_called_once_with("srv-1", edited)
    assert len(config_manager.saved) == 0


def test_remove_mcp_server_removes_from_registry_and_settings(caplog):
    config = _make_config("srv-1", "To Remove")
    settings = AppSettings(mcp_servers=[config])
    config_manager = FakeConfigManager()
    registry = MagicMock(spec=MCPServerRegistry)

    controller = McpServerSettingsController(
        settings_provider=lambda: settings,
        config_manager=config_manager,
        collections_provider=lambda: None,
        get_collections=lambda: [],
        environment_lookup=lambda _id: None,
        metrics=MagicMock(),
        template_service=MagicMock(),
        mcp_manager=MagicMock(),
        registry=registry,
    )

    with caplog.at_level(logging.INFO):
        controller.remove_mcp_server("srv-1")

    registry.remove.assert_called_once_with("srv-1")
    assert settings.mcp_servers == []
    assert "mcp_servers_persist_requested reason=remove count=0" in caplog.text


def test_start_and_stop_mcp_server():
    config = _make_config("srv-1", "Target", enabled=False)
    settings = AppSettings(mcp_servers=[config])
    config_manager = FakeConfigManager()
    registry = MagicMock(spec=MCPServerRegistry)

    controller = McpServerSettingsController(
        settings_provider=lambda: settings,
        config_manager=config_manager,
        collections_provider=lambda: None,
        get_collections=lambda: [],
        environment_lookup=lambda _id: None,
        metrics=MagicMock(),
        template_service=MagicMock(),
        mcp_manager=MagicMock(),
        registry=registry,
    )

    controller.start_mcp_server("srv-1")
    assert settings.mcp_servers[0].enabled is True
    registry.start.assert_called_once_with("srv-1")

    controller.stop_mcp_server("srv-1")
    assert settings.mcp_servers[0].enabled is False
    registry.stop.assert_called_once_with("srv-1")


def test_reconfiguration_finished_persists_when_committed():
    config = _make_config("srv-1", "Original")
    reconfigured = _make_config("srv-1", "Reconfigured")
    settings = AppSettings(mcp_servers=[config])
    config_manager = FakeConfigManager()
    registry = MagicMock(spec=MCPServerRegistry)
    registry.list_configurations.return_value = [reconfigured]

    controller = McpServerSettingsController(
        settings_provider=lambda: settings,
        config_manager=config_manager,
        collections_provider=lambda: None,
        get_collections=lambda: [],
        environment_lookup=lambda _id: None,
        metrics=MagicMock(),
        template_service=MagicMock(),
        mcp_manager=MagicMock(),
        registry=registry,
    )

    controller._on_mcp_server_reconfiguration_finished("srv-1", committed=True)
    assert settings.mcp_servers[0].name == "Reconfigured"
    assert len(config_manager.saved) == 1

    controller._on_mcp_server_reconfiguration_finished("srv-1", committed=False)
    assert len(config_manager.saved) == 1


def test_collection_by_id_uses_presenter_and_fallback():
    col_a = Collection(id="col-a", name="Collection A")
    col_b = Collection(id="col-b", name="Collection B")
    settings = AppSettings()
    config_manager = FakeConfigManager()
    registry = MagicMock(spec=MCPServerRegistry)

    presenter = MagicMock()
    presenter.collection_by_id.return_value = col_a

    controller = McpServerSettingsController(
        settings_provider=lambda: settings,
        config_manager=config_manager,
        collections_provider=lambda: presenter,
        get_collections=lambda: [col_b],
        environment_lookup=lambda _id: None,
        metrics=MagicMock(),
        template_service=MagicMock(),
        mcp_manager=MagicMock(),
        registry=registry,
    )

    assert controller._collection_by_id("col-a") == col_a
    presenter.collection_by_id.assert_called_once_with("col-a")

    controller_no_lookup = McpServerSettingsController(
        settings_provider=lambda: settings,
        config_manager=config_manager,
        collections_provider=lambda: object(),
        get_collections=lambda: [col_b],
        environment_lookup=lambda _id: None,
        metrics=MagicMock(),
        template_service=MagicMock(),
        mcp_manager=MagicMock(),
        registry=registry,
    )
    assert controller_no_lookup._collection_by_id("col-b") == col_b
    assert controller_no_lookup._collection_by_id("missing") is None


def test_start_enabled_and_stop_all():
    settings = AppSettings()
    config_manager = FakeConfigManager()
    registry = MagicMock(spec=MCPServerRegistry)

    controller = McpServerSettingsController(
        settings_provider=lambda: settings,
        config_manager=config_manager,
        collections_provider=lambda: None,
        get_collections=lambda: [],
        environment_lookup=lambda _id: None,
        metrics=MagicMock(),
        template_service=MagicMock(),
        mcp_manager=MagicMock(),
        registry=registry,
    )

    controller.start_enabled()
    registry.start_enabled.assert_called_once()

    controller.stop_all()
    registry.stop_all.assert_called_once()
