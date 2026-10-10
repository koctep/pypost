"""Contract, regression, and startup tests for Built-in MCP servers (PYPOST-1351)."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
from types import SimpleNamespace

import anyio
from PySide6.QtCore import QCoreApplication
import pytest
import time

from pypost.core.builtin_collections import BuiltinCollectionView
from pypost.core.library_connection_store import LibraryConnectionStore
from pypost.core.library_manager_service import LibraryManagerService
from pypost.core.local_overlay_manager import LocalOverlayManager
from pypost.core.mcp_server_registry import MCPServerRegistry
from pypost.core.predefined_library import PredefinedLibraryService
from pypost.core.qt.daemon_runtime import DaemonRuntime
from pypost.models.library_manifest import LocalLibraryOverlay
from pypost.models.models import Collection, Environment, RequestData
from pypost.models.settings import AppSettings, McpServerConfiguration
from pypost.ui.mcp_server_controller import McpServerSettingsController
from tests.helpers.mcp_live_server import free_port, wait_for_port
from tests.test_mcp_server_integration import _mcp_list_tools


pytestmark = pytest.mark.timeout(30)

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_ROOT = REPO_ROOT / "examples"


def _mcp_url(port: int) -> str:
    return f"http://127.0.0.1:{port}/mcp"


def _make_dummy_collection(coll_id: str, tool_name: str) -> Collection:
    return Collection(
        id=coll_id,
        name=tool_name,
        requests=[
            RequestData(
                id=f"{coll_id}-req",
                name=tool_name,
                method="GET",
                url="https://example.com/api",
                expose_as_mcp=True,
            )
        ],
    )


# ==============================================================================
# 1. Model Validation (AC 1 & AC 6)
# ==============================================================================


def test_builtin_server_model_validation() -> None:
    """Validate McpServerConfiguration rules for bundled_library flag."""
    # (a) Valid bundled configuration
    valid_builtin = McpServerConfiguration(
        id="jira-builtin",
        port=9001,
        environment_id="jira-env",
        bundled_library=True,
        library_id="pypost-examples",
        manifest_id="pypost-examples",
        library_collection_path="collections/jira_mcp.json",
    )
    assert valid_builtin.bundled_library is True
    assert valid_builtin.library_id == "pypost-examples"

    # (b) Default value of bundled_library is False
    omitted = McpServerConfiguration(
        id="default-flag",
        port=9002,
        environment_id="env-1",
        collection_id="col-1",
    )
    assert omitted.bundled_library is False

    # (c) bundled_library=True without library_id (or library_id=None) raises ValueError
    with pytest.raises(ValueError, match="bundled_library requires library_id"):
        McpServerConfiguration(
            id="bad-no-lib",
            port=9003,
            environment_id="env-1",
            bundled_library=True,
            collection_id="col-1",
        )

    with pytest.raises(ValueError, match="bundled_library requires library_id"):
        McpServerConfiguration(
            id="bad-none-lib",
            port=9004,
            environment_id="env-1",
            bundled_library=True,
            library_id=None,
            collection_id="col-1",
        )

    # (d) bundled_library=True with library_id != "pypost-examples" raises ValueError
    with pytest.raises(
        ValueError, match="bundled_library requires library_id 'pypost-examples'"
    ):
        McpServerConfiguration(
            id="bad-other-lib",
            port=9005,
            environment_id="env-1",
            bundled_library=True,
            library_id="other-lib",
            manifest_id="other-lib",
            library_collection_path="collections/jira_mcp.json",
        )

    # (e) Normal workspace server validates (bundled_library=False, collection_id set)
    workspace_cfg = McpServerConfiguration(
        id="workspace-srv",
        port=9006,
        environment_id="env-1",
        bundled_library=False,
        collection_id="col-workspace",
    )
    assert workspace_cfg.bundled_library is False
    assert workspace_cfg.collection_id == "col-workspace"

    # (f) Normal library server validates (bundled_library=False, library_id set)
    lib_cfg = McpServerConfiguration(
        id="custom-lib-srv",
        port=9007,
        environment_id="env-1",
        bundled_library=False,
        library_id="custom-lib",
        manifest_id="custom-lib",
        library_collection_path="collections/custom.json",
    )
    assert lib_cfg.bundled_library is False
    assert lib_cfg.library_id == "custom-lib"

    # (g) Legacy row carrying library_id and stale collection_id ignores collection_id
    legacy_cfg = McpServerConfiguration(
        id="legacy-srv",
        port=9008,
        environment_id="env-1",
        bundled_library=False,
        library_id="custom-lib",
        manifest_id="custom-lib",
        library_collection_path="collections/custom.json",
        collection_id="stale-col-id",
    )
    assert legacy_cfg.library_id == "custom-lib"
    assert legacy_cfg.collection_id == "stale-col-id"


# ==============================================================================
# 2. Built-in Server Startup and Exposed Tools (AC 1)
# ==============================================================================


def test_builtin_server_starts_and_exposes_tools() -> None:
    """An enabled Built-in MCP server starts under MCPServerRegistry and exposes tools."""
    port = free_port()
    env = Environment(
        id="jira-env",
        name="Jira Env",
        variables={"jira_base_url": "https://test.atlassian.net"},
    )
    registry = MCPServerRegistry(
        environment_lookup=lambda env_id: env if env_id == "jira-env" else None,
    )
    config = McpServerConfiguration(
        id="jira-builtin",
        port=port,
        environment_id="jira-env",
        bundled_library=True,
        library_id="pypost-examples",
        manifest_id="pypost-examples",
        library_collection_path="collections/jira_mcp.json",
        enabled=True,
    )
    registry.upsert(config)

    try:
        registry.start("jira-builtin")
        wait_for_port("127.0.0.1", port)
        assert registry.is_running("jira-builtin")
        assert registry.status("jira-builtin").state == "running"

        tools = anyio.run(_mcp_list_tools, _mcp_url(port))
        assert len(tools) > 0
        assert "jira_search_issues_jql" in tools or any("jira" in t for t in tools)
    finally:
        registry.stop_all()


# ==============================================================================
# 3. Dynamic Auto-update on Upgrade / Shipped Change (AC 2)
# ==============================================================================


def test_builtin_server_picks_up_collection_update_on_next_start(tmp_path: Path) -> None:
    """Updating collection data updates served tools on next start without modifying settings."""
    # Copy shipped examples into tmp_path to simulate an upgrade by mutating disk content
    bundle_copy = tmp_path / "bundle"
    shutil.copytree(EXAMPLES_ROOT, bundle_copy)

    predefined = PredefinedLibraryService(root=bundle_copy)
    builtin_view = BuiltinCollectionView(predefined=predefined)

    env = Environment(id="jira-env", variables={})
    registry = MCPServerRegistry(
        environment_lookup=lambda _id: env,
        builtin_view=builtin_view,
    )

    port = free_port()
    config = McpServerConfiguration(
        id="jira-builtin-upgrade",
        port=port,
        environment_id="jira-env",
        bundled_library=True,
        library_id="pypost-examples",
        manifest_id="pypost-examples",
        library_collection_path="collections/jira_mcp.json",
        enabled=True,
    )
    registry.upsert(config)

    try:
        # First start: initial tools
        registry.start("jira-builtin-upgrade")
        wait_for_port("127.0.0.1", port)
        tools_v1 = anyio.run(_mcp_list_tools, _mcp_url(port))
        assert "jira_search_issues_jql" in tools_v1
        assert "brand_new_tool" not in tools_v1
        registry.stop("jira-builtin-upgrade")

        # Simulate application upgrade: mutate collection file on disk
        target_json = bundle_copy / "collections" / "jira_mcp.json"
        data = json.loads(target_json.read_text(encoding="utf-8"))
        data["requests"].append({
            "id": "new-tool-req",
            "name": "Brand New Tool",
            "method": "GET",
            "url": "https://jira.example/new",
            "expose_as_mcp": True,
        })
        target_json.write_text(json.dumps(data), encoding="utf-8")

        # Second start: picks up updated tools without touching server configuration
        registry.start("jira-builtin-upgrade")
        wait_for_port("127.0.0.1", port)
        tools_v2 = anyio.run(_mcp_list_tools, _mcp_url(port))
        assert "brand_new_tool" in tools_v2
    finally:
        registry.stop_all()


# ==============================================================================
# 4. Isolation from User Overlays and Presets (AC 3)
# ==============================================================================


def test_builtin_server_isolated_from_user_library_overlay_and_preset(tmp_path: Path) -> None:
    """External user library named 'pypost-examples' with overlay/preset does not affect builtin."""
    port = free_port()
    # Create a user library in tmp_path with modified variable values
    user_lib_dir = tmp_path / "user_lib"
    user_coll_dir = user_lib_dir / "collections"
    user_coll_dir.mkdir(parents=True)
    (user_lib_dir / "pypost-library.json").write_text(
        json.dumps({
            "id": "pypost-examples",
            "name": "Malicious Shadow Library",
            "collections": ["collections/jira_mcp.json"],
            "variables": [
                {"name": "jira_base_url", "type": "string", "default": "https://malicious.example"}
            ],
            "presets": {"jira-env": {"jira_base_url": "https://preset-shadow.example"}},
        }),
        encoding="utf-8",
    )
    user_coll = Collection(
        id="jira-shadow",
        name="Shadow Collection",
        requests=[
            RequestData(
                id="shadow-req",
                name="Shadow Tool",
                method="GET",
                url="https://shadow.example/api",
                expose_as_mcp=True,
            )
        ],
    )
    (user_coll_dir / "jira_mcp.json").write_text(
        user_coll.model_dump_json(), encoding="utf-8"
    )

    overlay_mgr = LocalOverlayManager(tmp_path / "overlays")
    overlay_mgr.save_overlay(
        LocalLibraryOverlay(
            library_id="pypost-examples",
            overrides={"jira_base_url": "https://overlay-shadow.example"},
        )
    )

    user_lib_service = LibraryManagerService(
        connection_store=LibraryConnectionStore(tmp_path / "connections.json"),
        overlay_manager=overlay_mgr,
    )
    user_lib_service.connect_local_directory(user_lib_dir)

    # Shipped builtin server with legitimate workspace environment
    workspace_env = Environment(
        id="jira-env",
        name="Workspace Env",
        variables={"jira_base_url": "https://legit-workspace.example"},
    )

    registry = MCPServerRegistry(
        environment_lookup=lambda env_id: workspace_env if env_id == "jira-env" else None,
        library_service=user_lib_service,
    )

    config = McpServerConfiguration(
        id="jira-builtin",
        port=port,
        environment_id="jira-env",
        bundled_library=True,
        library_id="pypost-examples",
        manifest_id="pypost-examples",
        library_collection_path="collections/jira_mcp.json",
        enabled=True,
    )
    registry.upsert(config)

    try:
        registry.start("jira-builtin")
        wait_for_port("127.0.0.1", port)

        tools = anyio.run(_mcp_list_tools, _mcp_url(port))
        # Must NOT expose "shadow_tool" from user library
        assert "shadow_tool" not in tools
        # Must expose official tools
        assert any("jira" in t for t in tools)

        # Inspect runtime inputs
        manager = registry.manager_for("jira-builtin")
        # Ensure environment resolved legit-workspace.example, not overlay or preset
        if hasattr(manager, "_impl") and hasattr(manager._impl, "_variable_supplier"):
            actual_url = manager._impl._variable_supplier().get("jira_base_url")
            assert actual_url == "https://legit-workspace.example"
    finally:
        registry.stop_all()


# ==============================================================================
# 5. View Membership Diagnostic (AC 4)
# ==============================================================================


def test_builtin_server_missing_or_non_entry_path_reported_cleanly() -> None:
    """Non-entry paths or unknown paths report 'missing built-in collection' and fail to start."""
    env = Environment(id="env-1", variables={})
    registry = MCPServerRegistry(
        environment_lookup=lambda _id: env,
    )

    # (a) collections/mcp.json is declared in manifest but is NOT in builtin-collections.yaml
    non_entry_config = McpServerConfiguration(
        id="non-entry-srv",
        port=9011,
        environment_id="env-1",
        bundled_library=True,
        library_id="pypost-examples",
        manifest_id="pypost-examples",
        library_collection_path="collections/mcp.json",
        enabled=True,
    )
    registry.upsert(non_entry_config)
    registry.start("non-entry-srv")

    assert not registry.is_running("non-entry-srv")
    status = registry.status("non-entry-srv")
    assert status.state == "failed"
    assert "missing built-in collection" in status.message

    # (b) Unknown collection path
    unknown_config = McpServerConfiguration(
        id="unknown-srv",
        port=9012,
        environment_id="env-1",
        bundled_library=True,
        library_id="pypost-examples",
        manifest_id="pypost-examples",
        library_collection_path="collections/does_not_exist.json",
        enabled=True,
    )
    registry.upsert(unknown_config)
    registry.start("unknown-srv")

    assert not registry.is_running("unknown-srv")
    status_unk = registry.status("unknown-srv")
    assert status_unk.state == "failed"
    assert "missing built-in collection" in status_unk.message


# ==============================================================================
# 6. Backward Compatibility for Legacy Rows (AC 5)
# ==============================================================================


def test_runtime_regression_workspace_and_normal_library_servers(tmp_path: Path) -> None:
    """Workspace servers, ordinary library servers, and legacy rows load and start as before."""
    workspace_coll = _make_dummy_collection("ws-col", "Workspace Tool")
    workspace_env = Environment(id="ws-env", variables={"key": "ws-val"})

    user_lib_dir = tmp_path / "custom_lib"
    user_coll_dir = user_lib_dir / "collections"
    user_coll_dir.mkdir(parents=True)
    (user_lib_dir / "pypost-library.json").write_text(
        json.dumps({
            "id": "custom-lib",
            "name": "Custom Lib",
            "collections": ["collections/custom.json"],
            "variables": [{"name": "key", "type": "string", "default": "custom-val"}],
        }),
        encoding="utf-8",
    )
    custom_coll = _make_dummy_collection("custom-col", "Custom Tool")
    (user_coll_dir / "custom.json").write_text(
        custom_coll.model_dump_json(), encoding="utf-8"
    )

    lib_service = LibraryManagerService(
        connection_store=LibraryConnectionStore(tmp_path / "connections.json"),
        overlay_manager=LocalOverlayManager(tmp_path / "overlays"),
    )
    lib_service.connect_local_directory(user_lib_dir)

    collections_map = {workspace_coll.id: workspace_coll}
    environments_map = {workspace_env.id: workspace_env}

    registry = MCPServerRegistry(
        collection_lookup=collections_map.get,
        environment_lookup=environments_map.get,
        library_service=lib_service,
    )

    port_ws = free_port()
    port_lib = free_port()
    port_legacy = free_port()

    # (1) Normal workspace server
    cfg_ws = McpServerConfiguration(
        id="ws-srv",
        port=port_ws,
        collection_id=workspace_coll.id,
        environment_id=workspace_env.id,
        bundled_library=False,
        enabled=True,
    )

    # (2) Normal library server
    cfg_lib = McpServerConfiguration(
        id="lib-srv",
        port=port_lib,
        environment_id=workspace_env.id,
        library_id="custom-lib",
        manifest_id="custom-lib",
        library_collection_path="collections/custom.json",
        bundled_library=False,
        enabled=True,
    )

    # (3) Legacy library server with stale collection_id
    cfg_legacy = McpServerConfiguration(
        id="legacy-srv",
        port=port_legacy,
        environment_id=workspace_env.id,
        library_id="custom-lib",
        manifest_id="custom-lib",
        library_collection_path="collections/custom.json",
        collection_id="stale-col-id",
        bundled_library=False,
        enabled=True,
    )

    registry.upsert(cfg_ws)
    registry.upsert(cfg_lib)
    registry.upsert(cfg_legacy)

    try:
        registry.start("ws-srv")
        wait_for_port("127.0.0.1", port_ws)
        assert registry.is_running("ws-srv")
        tools_ws = anyio.run(_mcp_list_tools, _mcp_url(port_ws))
        assert "workspace_tool" in tools_ws

        registry.start("lib-srv")
        wait_for_port("127.0.0.1", port_lib)
        assert registry.is_running("lib-srv")
        tools_lib = anyio.run(_mcp_list_tools, _mcp_url(port_lib))
        assert "custom_tool" in tools_lib

        registry.start("legacy-srv")
        wait_for_port("127.0.0.1", port_legacy)
        assert registry.is_running("legacy-srv")
        tools_legacy = anyio.run(_mcp_list_tools, _mcp_url(port_legacy))
        assert "custom_tool" in tools_legacy
    finally:
        registry.stop_all()


# ==============================================================================
# 7. Daemon Runtime Starts Built-in Server Without Library Service (AC 7)
# ==============================================================================


def test_daemon_runtime_starts_builtin_server_without_library_service(tmp_path: Path) -> None:
    """In headless / DaemonRuntime context, an enabled Built-in server starts without mcp_failed."""
    port = free_port()
    env = Environment(
        id="jira-cloud-mcp-environment",
        name="Jira Env",
        variables={"jira_base_url": "https://test.atlassian.net"},
    )
    env_dir = tmp_path / "environments"
    env_dir.mkdir(parents=True)
    (env_dir / "environments.json").write_text(
        json.dumps([env.model_dump(mode="json")]), encoding="utf-8"
    )

    builtin_cfg = McpServerConfiguration(
        id="daemon-builtin-srv",
        port=port,
        environment_id=env.id,
        bundled_library=True,
        library_id="pypost-examples",
        manifest_id="pypost-examples",
        library_collection_path="collections/jira_mcp.json",
        enabled=True,
    )

    runtime = DaemonRuntime(
        SimpleNamespace(
            collections_dir=tmp_path / "collections",
            environments_dir=env_dir,
            collections_source="default",
            environments_source="default",
        ),
        startup_timeout_ms=5000,
        config_manager=SimpleNamespace(
            load_config_strict=lambda: AppSettings(mcp_servers=[builtin_cfg]),
        ),
    )

    try:
        runtime.start()
        app = QCoreApplication.instance() or QCoreApplication([])
        deadline = time.monotonic() + 5.0
        while not runtime.is_ready and time.monotonic() < deadline:
            app.processEvents()
            time.sleep(0.05)
        assert runtime.is_ready
        assert runtime.exit_code == 0
        wait_for_port("127.0.0.1", port)
        tools = anyio.run(_mcp_list_tools, _mcp_url(port))
        assert any("jira" in t for t in tools)
    finally:
        runtime.shutdown()


# ==============================================================================
# 8. Controller Construction Point with Injected Registry (AC 7)
# ==============================================================================


def test_mcp_server_settings_controller_with_injected_registry() -> None:
    """Instantiating and using McpServerSettingsController with registry works seamlessly."""
    port = free_port()
    env = Environment(id="env-1", variables={})
    registry = MCPServerRegistry(
        environment_lookup=lambda _id: env,
    )
    builtin_cfg = McpServerConfiguration(
        id="ctrl-builtin-srv",
        port=port,
        environment_id="env-1",
        bundled_library=True,
        library_id="pypost-examples",
        manifest_id="pypost-examples",
        library_collection_path="collections/jira_mcp.json",
        enabled=False,
    )
    settings = AppSettings(mcp_servers=[builtin_cfg])

    controller = McpServerSettingsController(
        settings_provider=lambda: settings,
        environment_lookup=lambda _id: env,
        registry=registry,
    )

    # Controller lists configs and statuses through injected registry
    configs = controller.mcp_server_configurations()
    assert len(configs) == 1
    assert configs[0].id == "ctrl-builtin-srv"
    assert configs[0].bundled_library is True

    statuses = controller.registry.list_statuses()
    assert len(statuses) == 1
    assert statuses[0].state == "stopped"

    # Start via controller / registry
    try:
        controller.start_mcp_server("ctrl-builtin-srv")
        wait_for_port("127.0.0.1", port)
        assert controller.registry.is_running("ctrl-builtin-srv")
        assert controller.registry.status("ctrl-builtin-srv").state == "running"
    finally:
        controller.registry.stop_all()


# ==============================================================================
# 9. Observability and Structured Logging (Step 6)
# ==============================================================================


def test_builtin_server_observability_and_logging(caplog: pytest.LogCaptureFixture) -> None:
    """Verify structured logs across DEBUG, INFO, WARNING and status diagnostics."""
    port = free_port()
    env = Environment(
        id="jira-env",
        name="Jira Env",
        variables={"jira_base_url": "https://test.atlassian.net"},
    )
    registry = MCPServerRegistry(
        environment_lookup=lambda env_id: env if env_id == "jira-env" else None,
    )
    valid_cfg = McpServerConfiguration(
        id="jira-builtin-obs",
        port=port,
        environment_id="jira-env",
        bundled_library=True,
        library_id="pypost-examples",
        manifest_id="pypost-examples",
        library_collection_path="collections/jira_mcp.json",
        enabled=True,
    )
    registry.upsert(valid_cfg)

    # 1. Startup and discovery logging
    with caplog.at_level("DEBUG"):
        try:
            registry.start("jira-builtin-obs")
            wait_for_port("127.0.0.1", port)
            assert registry.is_running("jira-builtin-obs")
            assert registry.status("jira-builtin-obs").state == "running"

            log_text = caplog.text
            # MCPServerRegistry lifecycle events
            assert "mcp_registry_start_requested" in log_text
            assert f"instance_id=jira-builtin-obs port={port}" in log_text
            assert "mcp_registry_status instance_id=jira-builtin-obs state=starting" in log_text
            assert "mcp_registry_status instance_id=jira-builtin-obs state=running" in log_text

            # PredefinedLibraryService discovery events
            assert "predefined_library_discovery_started library_id=pypost-examples" in log_text
            assert "predefined_library_discovery_completed library_id=pypost-examples" in log_text

            # BuiltinCollectionView listing events
            assert "builtin_collections_list_completed" in log_text
            assert "library_id=pypost-examples" in log_text
            assert "builtin_collection_entry_loaded" in log_text
        finally:
            registry.stop_all()
            assert "mcp_registry_stop_requested" in caplog.text
            assert "mcp_registry_status instance_id=jira-builtin-obs state=stopped" in caplog.text

    # 2. Failure diagnostic and status logging
    caplog.clear()
    invalid_cfg = McpServerConfiguration(
        id="bad-builtin-obs",
        port=9099,
        environment_id="jira-env",
        bundled_library=True,
        library_id="pypost-examples",
        manifest_id="pypost-examples",
        library_collection_path="collections/mcp.json",  # Not in builtin-collections.yaml
        enabled=True,
    )
    registry.upsert(invalid_cfg)

    with caplog.at_level("INFO"):
        registry.start("bad-builtin-obs")
        assert not registry.is_running("bad-builtin-obs")

        status = registry.status("bad-builtin-obs")
        assert status.state == "failed"
        assert "missing built-in collection" in status.message

        fail_logs = [r for r in caplog.records if "bad-builtin-obs" in r.message]
        assert any(
            "mcp_registry_status instance_id=bad-builtin-obs state=failed" in r.message
            for r in fail_logs
        )

