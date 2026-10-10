"""Automated failing repro tests for Built-in MCP server lifecycle and controller save.

Task: PYPOST-1352 / Epic: PYPOST-1335
Tests acceptance criteria 1 through 8:
1. Built-in server survives reconcile_references with or without valid_collection_ids.
2. Built-in server stops with missing environment message on environment deletion.
3. Built-in server reconfigure on a running row transitions smoothly without collection error.
4. Built-in server refresh_environment preserves manifest defaults for omitted keys.
5. Controller upsert_mcp_server resolves bundled examples even when user library exists.
6. Controller upsert_mcp_server never writes overlay files (overlay={}).
7. Controller upsert_mcp_server rejects uncurated collection paths with builtin_invalid.
8. Ordinary library and workspace server rows remain unchanged (regression safety).
"""

from __future__ import annotations

import json
from pathlib import Path

import anyio
import pytest

from pypost.core.library_connection_store import LibraryConnectionStore
from pypost.core.library_manager_service import LibraryManagerService
from pypost.core.local_overlay_manager import LocalOverlayManager
from pypost.core.mcp_server_registry import MCPServerRegistry
from pypost.models.models import Collection, Environment, RequestData
from pypost.models.settings import AppSettings, McpServerConfiguration
from pypost.ui.mcp_server_controller import McpServerSettingsController
from tests.helpers.mcp_live_server import free_port, wait_for_port
from tests.test_mcp_server_integration import _mcp_list_tools

pytestmark = pytest.mark.timeout(30)


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
# AC 1: Built-in server survives reconcile_references
# ==============================================================================


def test_builtin_server_survives_reconcile_references() -> None:
    """A running Built-in row stays running after reconcile_references with various collection IDs.

    Built-in rows have collection_id=None. Workspace collection updates (e.g. empty set
    or set of other IDs) must NOT drop or stop the running Built-in server.
    """
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
        id="jira-builtin-reconcile",
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
        registry.start("jira-builtin-reconcile")
        wait_for_port("127.0.0.1", port)
        assert registry.is_running("jira-builtin-reconcile")

        # Case A: reconcile_references with valid_collection_ids={"other-id"}
        changed = registry.reconcile_references(
            valid_collection_ids={"other-id"},
            valid_environment_ids={"jira-env"},
        )
        assert changed is False
        assert registry.is_running("jira-builtin-reconcile")
        assert registry.status("jira-builtin-reconcile").state == "running"

        # Case B: reconcile_references with empty collection set
        changed = registry.reconcile_references(
            valid_collection_ids=set(),
            valid_environment_ids={"jira-env"},
        )
        assert changed is False
        assert registry.is_running("jira-builtin-reconcile")
        assert registry.status("jira-builtin-reconcile").state == "running"
    finally:
        registry.stop_all()


# ==============================================================================
# AC 2: Built-in server stops on environment deletion
# ==============================================================================


def test_builtin_server_stops_on_environment_deletion() -> None:
    """A running Built-in row stops with failed status and 'missing environment' on env deletion."""
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
        id="jira-builtin-env-del",
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
        registry.start("jira-builtin-env-del")
        wait_for_port("127.0.0.1", port)
        assert registry.is_running("jira-builtin-env-del")

        # Simulate environment deletion by removing jira-env from valid_environment_ids
        changed = registry.reconcile_references(
            valid_collection_ids=set(),
            valid_environment_ids=set(),
        )
        assert changed is True
        assert not registry.is_running("jira-builtin-env-del")

        status = registry.status("jira-builtin-env-del")
        assert status.state == "failed"
        assert "missing environment" in status.message
    finally:
        registry.stop_all()


# ==============================================================================
# AC 3: Reconfigure running Built-in row
# ==============================================================================


def test_builtin_server_reconfigure_running_row() -> None:
    """Calling reconfigure on a running Built-in row transitions without raising error."""
    port_a = free_port()
    port_b = free_port()
    env = Environment(
        id="jira-env",
        name="Jira Env",
        variables={"jira_base_url": "https://test.atlassian.net"},
    )
    registry = MCPServerRegistry(
        environment_lookup=lambda env_id: env if env_id == "jira-env" else None,
    )
    config_a = McpServerConfiguration(
        id="jira-builtin-reconf",
        port=port_a,
        environment_id="jira-env",
        bundled_library=True,
        library_id="pypost-examples",
        manifest_id="pypost-examples",
        library_collection_path="collections/jira_mcp.json",
        enabled=True,
    )
    registry.upsert(config_a)

    try:
        registry.start("jira-builtin-reconf")
        wait_for_port("127.0.0.1", port_a)
        assert registry.is_running("jira-builtin-reconf")

        # Reconfigure to port_b
        config_b = config_a.model_copy(update={"port": port_b})
        registry.reconfigure("jira-builtin-reconf", config_b)
        wait_for_port("127.0.0.1", port_b)

        assert registry.is_running("jira-builtin-reconf")
        assert registry.status("jira-builtin-reconf").state == "running"
        tools = anyio.run(_mcp_list_tools, _mcp_url(port_b))
        assert len(tools) > 0
    finally:
        registry.stop_all()


# ==============================================================================
# AC 4: Refresh environment preserves manifest defaults
# ==============================================================================


def test_builtin_server_refresh_environment_preserves_manifest_defaults() -> None:
    """After refresh_environment(env_id), variable snapshot keeps manifest defaults."""
    port = free_port()
    # Shipped manifest has jira_base_url, jira_project_key (default "PROJ"), jira_credentials.
    # The environment defines only jira_base_url initially.
    env = Environment(
        id="jira-env",
        name="Jira Env",
        variables={"jira_base_url": "https://custom.atlassian.net"},
    )
    registry = MCPServerRegistry(
        environment_lookup=lambda env_id: env if env_id == "jira-env" else None,
    )
    config = McpServerConfiguration(
        id="jira-builtin-refresh",
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
        registry.start("jira-builtin-refresh")
        wait_for_port("127.0.0.1", port)
        assert registry.is_running("jira-builtin-refresh")

        # Update environment: change jira_base_url, omit jira_project_key
        env.variables["jira_base_url"] = "https://updated.atlassian.net"
        registry.refresh_environment("jira-env")

        # The manager's variable supplier must return the updated URL AND the manifest default PROJ
        manager = registry.manager_for("jira-builtin-refresh")
        vars_snapshot = manager._variable_supplier()
        assert vars_snapshot.get("jira_base_url") == "https://updated.atlassian.net"
        assert vars_snapshot.get("jira_project_key") == "PROJ"
    finally:
        registry.stop_all()


# ==============================================================================
# AC 5: Controller upsert isolated from connected clone
# ==============================================================================


def test_controller_upsert_builtin_server_isolated_from_connected_clone(tmp_path: Path) -> None:
    """controller.upsert_mcp_server validates against bundled examples even with user clone."""
    port = free_port()
    # Create an external user library named "pypost-examples"
    user_lib_dir = tmp_path / "user_lib"
    user_coll_dir = user_lib_dir / "collections"
    user_coll_dir.mkdir(parents=True)
    (user_lib_dir / "pypost-library.json").write_text(
        json.dumps({
            "id": "pypost-examples",
            "name": "User Clone",
            "collections": ["collections/custom.json"],
            "variables": [],
        }),
        encoding="utf-8",
    )
    user_coll = _make_dummy_collection("custom-col", "Custom Tool")
    (user_coll_dir / "custom.json").write_text(
        user_coll.model_dump_json(), encoding="utf-8"
    )

    overlay_mgr = LocalOverlayManager(tmp_path / "overlays")
    user_lib_service = LibraryManagerService(
        connection_store=LibraryConnectionStore(tmp_path / "connections.json"),
        overlay_manager=overlay_mgr,
    )
    user_lib_service.connect_local_directory(user_lib_dir)

    env = Environment(
        id="jira-env",
        name="Jira Env",
        variables={"jira_base_url": "https://test.atlassian.net"},
    )
    registry = MCPServerRegistry(
        environment_lookup=lambda env_id: env if env_id == "jira-env" else None,
        library_service=user_lib_service,
    )
    settings = AppSettings()
    controller = McpServerSettingsController(
        settings_provider=lambda: settings,
        environment_lookup=lambda env_id: env if env_id == "jira-env" else None,
        registry=registry,
        library_service=user_lib_service,
    )

    builtin_cfg = McpServerConfiguration(
        id="jira-builtin-clone-test",
        port=port,
        environment_id="jira-env",
        bundled_library=True,
        library_id="pypost-examples",
        manifest_id="pypost-examples",
        library_collection_path="collections/jira_mcp.json",
        enabled=False,
    )

    # Calling upsert_mcp_server must validate against bundled adapter, succeeding
    controller.upsert_mcp_server(builtin_cfg)
    assert len(settings.mcp_servers) == 1
    assert settings.mcp_servers[0].id == "jira-builtin-clone-test"
    assert registry.configuration("jira-builtin-clone-test") is not None


# ==============================================================================
# AC 6: Controller upsert never touches overlay file
# ==============================================================================


def test_controller_upsert_builtin_server_never_touches_overlay_file(tmp_path: Path) -> None:
    """controller.upsert_mcp_server(builtin_config) never creates/modifies overlay file."""
    port = free_port()
    overlay_dir = tmp_path / "overlays"
    overlay_mgr = LocalOverlayManager(overlay_dir)
    lib_service = LibraryManagerService(
        connection_store=LibraryConnectionStore(tmp_path / "connections.json"),
        overlay_manager=overlay_mgr,
    )

    env = Environment(
        id="jira-env",
        name="Jira Env",
        variables={"jira_base_url": "https://test.atlassian.net"},
    )
    registry = MCPServerRegistry(
        environment_lookup=lambda env_id: env if env_id == "jira-env" else None,
        library_service=lib_service,
    )
    settings = AppSettings()
    controller = McpServerSettingsController(
        settings_provider=lambda: settings,
        environment_lookup=lambda env_id: env if env_id == "jira-env" else None,
        registry=registry,
        library_service=lib_service,
    )

    builtin_cfg = McpServerConfiguration(
        id="jira-builtin-no-overlay",
        port=port,
        environment_id="jira-env",
        bundled_library=True,
        library_id="pypost-examples",
        manifest_id="pypost-examples",
        library_collection_path="collections/jira_mcp.json",
        enabled=False,
    )

    controller.upsert_mcp_server(builtin_cfg)

    # Check that overlay directory contains no files for pypost-examples
    example_overlay = overlay_dir / "pypost-examples" / "overlay.json"
    assert not example_overlay.exists()
    assert list(overlay_dir.glob("**/*.json")) == []


# ==============================================================================
# AC 7: Controller upsert rejects uncurated path
# ==============================================================================


def test_controller_upsert_builtin_server_rejects_uncurated_path() -> None:
    """controller.upsert_mcp_server(uncurated_config) raises ValueError matching builtin_invalid."""
    env = Environment(
        id="jira-env",
        name="Jira Env",
        variables={"jira_base_url": "https://test.atlassian.net"},
    )
    registry = MCPServerRegistry(
        environment_lookup=lambda env_id: env if env_id == "jira-env" else None,
    )
    settings = AppSettings()
    controller = McpServerSettingsController(
        settings_provider=lambda: settings,
        environment_lookup=lambda env_id: env if env_id == "jira-env" else None,
        registry=registry,
    )

    # collections/mcp.json is not in builtin-collections.yaml
    uncurated_cfg = McpServerConfiguration(
        id="bad-curated-srv",
        port=9098,
        environment_id="jira-env",
        bundled_library=True,
        library_id="pypost-examples",
        manifest_id="pypost-examples",
        library_collection_path="collections/mcp.json",
        enabled=False,
    )

    with pytest.raises(ValueError, match="builtin_invalid"):
        controller.upsert_mcp_server(uncurated_cfg)


# ==============================================================================
# AC 8: Ordinary library and workspace rows regression
# ==============================================================================


def test_ordinary_library_and_workspace_rows_regression(tmp_path: Path) -> None:
    """Ordinary workspace and library server rows save, reconfigure, and reconcile unchanged."""
    ws_coll = _make_dummy_collection("ws-col-reg", "Workspace Tool")
    ws_env = Environment(id="ws-env-reg", variables={"key": "ws-val"})

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

    collections_map = {ws_coll.id: ws_coll}
    environments_map = {ws_env.id: ws_env}

    registry = MCPServerRegistry(
        collection_lookup=collections_map.get,
        environment_lookup=environments_map.get,
        library_service=lib_service,
    )

    settings = AppSettings()
    controller = McpServerSettingsController(
        settings_provider=lambda: settings,
        collection_lookup=collections_map.get,
        environment_lookup=environments_map.get,
        registry=registry,
        library_service=lib_service,
    )

    port_ws = free_port()
    ws_cfg = McpServerConfiguration(
        id="ws-srv-reg",
        port=port_ws,
        collection_id=ws_coll.id,
        environment_id=ws_env.id,
        bundled_library=False,
        enabled=True,
    )

    # 1. Upsert workspace server
    controller.upsert_mcp_server(ws_cfg)
    assert len(settings.mcp_servers) == 1
    assert registry.configuration("ws-srv-reg") is not None

    try:
        registry.start("ws-srv-reg")
        wait_for_port("127.0.0.1", port_ws)
        assert registry.is_running("ws-srv-reg")

        # Reconcile with valid collection keeps it running
        registry.reconcile_references(
            valid_collection_ids={ws_coll.id},
            valid_environment_ids={ws_env.id},
        )
        assert registry.is_running("ws-srv-reg")

        # Reconcile without ws_coll stops it
        changed = registry.reconcile_references(
            valid_collection_ids=set(),
            valid_environment_ids={ws_env.id},
        )
        assert changed is True
        assert not registry.is_running("ws-srv-reg")
    finally:
        registry.stop_all()


# ==============================================================================
# AC 9: Observability and Logging (Step 6)
# ==============================================================================


def test_builtin_lifecycle_observability_and_logging(caplog: pytest.LogCaptureFixture) -> None:
    """Verify structured logging and diagnostic messages across lifecycle operations."""
    import logging

    port = free_port()
    env = Environment(
        id="jira-env-obs",
        name="Jira Env",
        variables={"jira_base_url": "https://test.atlassian.net"},
    )
    registry = MCPServerRegistry(
        environment_lookup=lambda env_id: env if env_id == "jira-env-obs" else None,
    )
    settings = AppSettings()
    controller = McpServerSettingsController(
        settings_provider=lambda: settings,
        environment_lookup=lambda env_id: env if env_id == "jira-env-obs" else None,
        registry=registry,
    )

    config = McpServerConfiguration(
        id="jira-obs-lifecycle",
        port=port,
        environment_id="jira-env-obs",
        bundled_library=True,
        library_id="pypost-examples",
        manifest_id="pypost-examples",
        library_collection_path="collections/jira_mcp.json",
        enabled=True,
    )

    # 1. Controller upsert logging
    with caplog.at_level(logging.INFO):
        controller.upsert_mcp_server(config)
        assert "mcp_library_save_committed" in caplog.text

    # 2. Registry start and status logging
    caplog.clear()
    with caplog.at_level(logging.INFO):
        try:
            registry.start("jira-obs-lifecycle")
            wait_for_port("127.0.0.1", port)
            assert registry.wait_for_state("jira-obs-lifecycle", "running", timeout=5.0)
            assert registry.is_running("jira-obs-lifecycle")

            assert "mcp_registry_start_requested" in caplog.text
            assert f"instance_id=jira-obs-lifecycle port={port}" in caplog.text
            assert (
                "mcp_registry_status instance_id=jira-obs-lifecycle state=running"
                in caplog.text
            )

            # 3. Environment deletion triggers reconcile status failed with diagnostic
            caplog.clear()
            changed = registry.reconcile_references(
                valid_collection_ids=set(),
                valid_environment_ids=set(),
            )
            assert changed is True
            assert not registry.is_running("jira-obs-lifecycle")
            status = registry.status("jira-obs-lifecycle")
            assert status.state == "failed"
            assert "missing environment" in status.message
            assert "mcp_registry_stop_requested" in caplog.text
            assert (
                "mcp_registry_status instance_id=jira-obs-lifecycle state=failed"
                in caplog.text
            )

        finally:
            registry.stop_all()

