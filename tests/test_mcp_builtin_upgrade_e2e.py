"""Offline connected acceptance of shipped upgrades and independent workspace copies."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import anyio
import pytest
from PySide6.QtWidgets import QApplication, QDialogButtonBox, QPushButton

from pypost.core.builtin_collections import BuiltinCollectionView
from pypost.core.config_manager import ConfigManager
from pypost.core.mcp_server_registry import MCPServerRegistry
from pypost.core.predefined_library import PredefinedLibraryService
from pypost.core.qt.mcp_server import MCPServerManager
from pypost.core.request_manager import RequestManager
from pypost.core.storage import StorageManager
from pypost.models.models import Collection, Environment, RequestData
from pypost.models.settings import AppSettings
from pypost.ui.dialogs.mcp_servers_dialog import _McpServerEditor
from pypost.ui.mcp_server_controller import McpServerSettingsController
from pypost.ui.presenters.collections_presenter import CollectionsPresenter
from pypost.ui.presenters.env_presenter import EnvPresenter
from tests.helpers.collections_tree import FakeStateManager
from tests.helpers.process_until import process_until

pytestmark = pytest.mark.timeout(60)
COLLECTION_PATH = "collections/test.json"
ENVIRONMENT_PATH = "environments/test.json"


class RecordingMCPServerManager(MCPServerManager):
    """Replace socket/thread transport only; keep the real tool implementation."""

    def start_server(self, port: int, tools: Any, host: str = "127.0.0.1") -> None:
        self._impl.register_tools(tools)
        self._startup_notified = True
        self.status_changed.emit(True)

    def stop_server(self) -> None:
        self._startup_notified = False
        self.status_changed.emit(False)

    def is_running(self) -> bool:
        return self._startup_notified


def write_bundle(root: Path, version: str, names: list[str]) -> None:
    (root / "collections").mkdir(parents=True)
    (root / "environments").mkdir()
    collection = Collection(
        id="shipped", name="Shipped API", version=version,
        requests=[RequestData(
            id=f"shipped-{name}", name=name, url="https://example.invalid/{{URL}}",
            expose_as_mcp=True, mcp_description=f"{version} {name}",
        ) for name in names],
    )
    (root / COLLECTION_PATH).write_text(collection.model_dump_json(), encoding="utf-8")
    environment = Environment(
        name="Paired", variables={"URL": "items", "TOKEN": "PLACEHOLDER"},
        hidden_keys={"TOKEN"}, mcp_overridable_keys={"URL"},
    )
    (root / ENVIRONMENT_PATH).write_text(
        json.dumps([environment.model_dump(mode="json")]), encoding="utf-8"
    )
    (root / "pypost-library.yaml").write_text(
        'schema_version: "1.0.0"\nid: pypost-examples\nname: Offline bundle\n'
        f'version: "{version}"\ncollections: [collections/test.json]\n', encoding="utf-8",
    )
    (root / "builtin-collections.yaml").write_text(
        'entries:\n  - collection: collections/test.json\n'
        '    environment: environments/test.json\n    name: Shipped MCP\n', encoding="utf-8",
    )


def click(editor: _McpServerEditor, text: str) -> None:
    buttons = [button for button in editor.findChildren(QPushButton) if button.text() == text]
    assert len(buttons) == 1 and buttons[0].isEnabled()
    buttons[0].click()


def listed_tools(registry: MCPServerRegistry, server_id: str) -> list[Any]:
    manager = registry.manager_for(server_id)
    assert isinstance(manager, RecordingMCPServerManager)
    return anyio.run(manager._impl.list_tools)


def test_builtin_upgrade_then_workspace_copy_remains_usable(
    qapp: QApplication, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("pypost.core.storage.user_data_dir", lambda *args: str(tmp_path / "data"))
    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_ENABLED", raising=False)
    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_KEY", raising=False)
    monkeypatch.setattr(
        "pypost.core.mcp_server_registry.MCPServerManager", RecordingMCPServerManager
    )
    root = tmp_path / "bundle"
    write_bundle(root, "1.0.0", ["Original"])
    view = BuiltinCollectionView(PredefinedLibraryService(root=root))
    storage = StorageManager()
    config = ConfigManager(config_dir=tmp_path / "config")
    settings = AppSettings(env_encryption_enabled=False)
    collections = CollectionsPresenter(
        RequestManager(storage), FakeStateManager(), storage=storage
    )
    legacy_manager = RecordingMCPServerManager()
    environments = EnvPresenter(
        storage, config, legacy_manager, settings,
        collections._request_manager.get_collections, None,
    )
    registry = MCPServerRegistry(
        collection_lookup=collections.collection_by_id,
        environment_lookup=environments.environment_by_id, builtin_view=view,
    )
    controller = McpServerSettingsController(
        settings_provider=lambda: settings, config_manager=config, registry=registry,
        collection_lookup=collections.collection_by_id,
        environment_lookup=environments.environment_by_id, mcp_manager=legacy_manager,
        library_service=registry._bundled_adapter,
    )
    editors = []

    def open_editor(configuration: Any = None) -> _McpServerEditor:
        editor = _McpServerEditor(
            collections=collections._request_manager.get_collections(),
            environments=list(environments._environments), configuration=configuration,
            default_environment=None, default_host="127.0.0.1", default_port=1080,
            builtin_view=view, create_environment=environments.create_workspace_environment,
            get_environments=lambda: list(environments._environments),
            create_collection=collections.create_workspace_collection,
            get_collections=collections._request_manager.get_collections,
        )
        editors.append(editor)
        editor.show()
        return editor

    try:
        editor = open_editor()
        editor._collection_source.setCurrentIndex(editor._collection_source.findData("builtin"))
        before = (root / ENVIRONMENT_PATH).read_bytes()
        click(editor, "Create editable copy of paired environment")
        process_until(lambda: len(environments._environments) == 1, timeout_ms=5000)
        paired = storage.load_environments()[0]
        assert paired.id == editor._environment.currentData()
        assert paired.variables == {"URL": "items", "TOKEN": ""}
        assert paired.hidden_keys == {"TOKEN"} and paired.mcp_overridable_keys == {"URL"}
        assert paired.builtin_environment_path == ENVIRONMENT_PATH
        assert (root / ENVIRONMENT_PATH).read_bytes() == before
        editor.findChild(QDialogButtonBox).button(QDialogButtonBox.StandardButton.Save).click()
        assert editor.result() == 1
        controller.upsert_mcp_server(editor.configuration())
        bundled = config.load_config_strict().mcp_servers[0]
        assert bundled.bundled_library and bundled.environment_id == paired.id
        assert bundled.library_collection_path == COLLECTION_PATH
        controller.start_mcp_server(bundled.id)
        assert registry.status(bundled.id).state == "running"
        assert [tool.name for tool in listed_tools(registry, bundled.id)] == ["original"]
        manager = registry.manager_for(bundled.id)
        assert manager._impl._variable_supplier() == paired.variables
        assert manager._impl._hidden_keys_supplier() == paired.hidden_keys
        controller.stop_mcp_server(bundled.id)

        replacement = tmp_path / "replacement"
        write_bundle(replacement, "2.0.0", ["Updated", "Added"])
        root.rename(tmp_path / "previous-bundle")
        replacement.rename(root)
        assert config.load_config_strict().mcp_servers[0] == bundled
        controller.start_mcp_server(bundled.id)
        tools = listed_tools(registry, bundled.id)
        assert {tool.name for tool in tools} == {"updated", "added"}
        assert {tool.description for tool in tools} == {"2.0.0 Updated", "2.0.0 Added"}
        controller.stop_mcp_server(bundled.id)

        editor = open_editor(bundled)
        source_bytes = (root / COLLECTION_PATH).read_bytes()
        click(editor, "Copy for editing")
        copied = storage.load_collections()[0]
        shipped = view.load_collection(COLLECTION_PATH)
        assert copied.version == "2.0.0"
        assert [request.model_dump(exclude={"id"}) for request in copied.requests] == (
            [request.model_dump(exclude={"id"}) for request in shipped.requests]
        )
        assert copied.id == editor._collection.currentData() and copied.id != "shipped"
        assert editor._collection_source.currentData() == "workspace"
        assert editor._environment.currentData() == paired.id and copied.library_link is None
        assert collections.collection_by_id(copied.id).model_dump() == copied.model_dump()
        assert collections.widget.model().rowCount() == 1
        for request in copied.requests:
            assert collections._request_manager.find_request(request.id)[1].id == copied.id
        assert (root / COLLECTION_PATH).read_bytes() == source_bytes
        assert config.load_config_strict().mcp_servers[0] == bundled
        editor.findChild(QDialogButtonBox).button(QDialogButtonBox.StandardButton.Save).click()
        assert editor.result() == 1
        controller.upsert_mcp_server(editor.configuration())
        workspace = config.load_config_strict().mcp_servers[0]
        assert workspace.id == bundled.id and workspace.collection_id == copied.id
        assert not workspace.bundled_library and workspace.environment_id == paired.id
        assert workspace.library_id is workspace.manifest_id is None
        assert workspace.library_collection_path is workspace.library_collection_index is None
        root.rename(tmp_path / "removed-bundle")
        controller.start_mcp_server(workspace.id)
        assert registry.status(workspace.id).state == "running"
        assert {tool.name for tool in listed_tools(registry, workspace.id)} == {"updated", "added"}
        assert registry.manager_for(workspace.id)._impl._variable_supplier() == paired.variables
    finally:
        for editor in editors:
            editor.close()
        registry.clear()
        assert environments.wait_storage_idle(timeout_ms=5000)
        assert environments.teardown(timeout_ms=5000).outcome == "success"
        assert collections.teardown(timeout_ms=5000)
        collections.widget.close()
