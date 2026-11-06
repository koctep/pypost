"""Automated failing repro tests for ordinary library MCP server lifecycle.

Task: PYPOST-1347 / Epic: PYPOST-1335
Architecture: ai-tasks/PYPOST-1347/20-architecture.md

Covers:
1. Ordinary library server survives reconcile_references ignoring workspace collections.
2. Ordinary library server stops when the library collection no longer resolves.
3. Ordinary library server reconfigure on a running row without workspace collection error.
4. Ordinary library refresh_environment preserves LibraryRuntimeResolver layers.
5. Workspace row reconcile/refresh semantics remain unchanged (regression guard).
6. Structured observability for ordinary library reconcile stop and env refresh.
"""

from __future__ import annotations

import logging
from pathlib import Path

import anyio
import pytest

from pypost.core.library_runtime_resolver import LibraryRuntimeResolver
from pypost.core.mcp_server_registry import MCPServerRegistry
from pypost.models.models import Collection, Environment, RequestData
from pypost.models.settings import McpServerConfiguration
from tests.helpers.mcp_live_server import free_port, wait_for_port
from tests.test_mcp_server_integration import _mcp_list_tools
from tests.test_mcp_standalone_execution_repro import _create_test_library

pytestmark = pytest.mark.timeout(30)


def _mcp_url(port: int) -> str:
    return f"http://127.0.0.1:{port}/mcp"


def _make_workspace_collection(coll_id: str, tool_name: str) -> Collection:
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


def _ordinary_library_config(
    *,
    instance_id: str,
    port: int,
    selection: dict,
    environment_id: str,
) -> McpServerConfiguration:
    return McpServerConfiguration(
        id=instance_id,
        port=port,
        environment_id=environment_id,
        library_id=selection["library_id"],
        manifest_id=selection["manifest_id"],
        library_collection_path=selection["path"],
        library_collection_index=selection["index"],
        collection_id=None,
        bundled_library=False,
        enabled=True,
    )


# ==============================================================================
# Defect 1 — Reconcile survival / collection-resolve stop
# ==============================================================================


def test_ordinary_library_server_survives_reconcile_references(tmp_path: Path) -> None:
    """Running ordinary library row stays running when workspace collection ids change."""
    service, selection = _create_test_library(tmp_path)
    port = free_port()
    env = Environment(
        id="lib-env",
        name="Library Env",
        variables={"note": "workspace-only"},
    )
    registry = MCPServerRegistry(
        environment_lookup=lambda env_id: env if env_id == "lib-env" else None,
        library_service=service,
    )
    config = _ordinary_library_config(
        instance_id="ordinary-lib-reconcile",
        port=port,
        selection=selection,
        environment_id="lib-env",
    )
    registry.upsert(config)

    try:
        registry.start("ordinary-lib-reconcile")
        wait_for_port("127.0.0.1", port)
        assert registry.is_running("ordinary-lib-reconcile")

        changed = registry.reconcile_references(
            valid_collection_ids=set(),
            valid_environment_ids={"lib-env"},
        )
        assert changed is False
        assert registry.is_running("ordinary-lib-reconcile")
        assert registry.status("ordinary-lib-reconcile").state == "running"
        assert "missing collection" not in registry.status("ordinary-lib-reconcile").message

        changed = registry.reconcile_references(
            valid_collection_ids={"unrelated-workspace-id"},
            valid_environment_ids={"lib-env"},
        )
        assert changed is False
        assert registry.is_running("ordinary-lib-reconcile")
        assert registry.status("ordinary-lib-reconcile").state == "running"
        assert "missing collection" not in registry.status("ordinary-lib-reconcile").message
    finally:
        registry.stop_all()


def test_ordinary_library_server_stops_when_library_collection_missing(
    tmp_path: Path,
) -> None:
    """Reconcile stops ordinary library rows when the selected collection file vanishes."""
    service, selection = _create_test_library(tmp_path)
    port = free_port()
    env = Environment(
        id="lib-env",
        name="Library Env",
        variables={"note": "workspace-only"},
    )
    registry = MCPServerRegistry(
        environment_lookup=lambda env_id: env if env_id == "lib-env" else None,
        library_service=service,
    )
    config = _ordinary_library_config(
        instance_id="ordinary-lib-coll-missing",
        port=port,
        selection=selection,
        environment_id="lib-env",
    )
    registry.upsert(config)

    try:
        registry.start("ordinary-lib-coll-missing")
        wait_for_port("127.0.0.1", port)
        assert registry.is_running("ordinary-lib-coll-missing")

        connection = service.get_connection(selection["library_id"])
        assert connection is not None
        collection_path = Path(connection.local_path) / selection["path"]
        assert collection_path.is_file()
        collection_path.unlink()

        changed = registry.reconcile_references(
            valid_collection_ids=set(),
            valid_environment_ids={"lib-env"},
        )
        assert changed is True
        assert not registry.is_running("ordinary-lib-coll-missing")

        status = registry.status("ordinary-lib-coll-missing")
        assert status.state == "failed"
        message = status.message.lower()
        # Library-context diagnostic (not bare workspace "missing collection").
        assert "collection" in message
        assert "library" in message
    finally:
        registry.stop_all()


# ==============================================================================
# Defect 2 — Reconfigure
# ==============================================================================


def test_ordinary_library_server_reconfigure_running_row(tmp_path: Path) -> None:
    """Reconfigure moves an ordinary library row to a new port without collection errors."""
    service, selection = _create_test_library(tmp_path)
    port_a = free_port()
    port_b = free_port()
    env = Environment(
        id="lib-env",
        name="Library Env",
        variables={"note": "workspace-only"},
    )
    registry = MCPServerRegistry(
        environment_lookup=lambda env_id: env if env_id == "lib-env" else None,
        library_service=service,
    )
    config_a = _ordinary_library_config(
        instance_id="ordinary-lib-reconf",
        port=port_a,
        selection=selection,
        environment_id="lib-env",
    )
    registry.upsert(config_a)

    try:
        registry.start("ordinary-lib-reconf")
        wait_for_port("127.0.0.1", port_a)
        assert registry.is_running("ordinary-lib-reconf")

        config_b = config_a.model_copy(update={"port": port_b})
        registry.reconfigure("ordinary-lib-reconf", config_b)
        wait_for_port("127.0.0.1", port_b)

        assert registry.is_running("ordinary-lib-reconf")
        assert registry.status("ordinary-lib-reconf").state == "running"
        tools = anyio.run(_mcp_list_tools, _mcp_url(port_b))
        assert len(tools) > 0
    finally:
        registry.stop_all()


# ==============================================================================
# Defect 3 — Environment refresh preserves library layers
# ==============================================================================


def test_ordinary_library_server_refresh_environment_preserves_library_layers(
    tmp_path: Path,
) -> None:
    """refresh_environment keeps manifest defaults equal to a fresh LibraryRuntimeResolver."""
    service, selection = _create_test_library(tmp_path)
    port = free_port()
    # Workspace env omits library default ``base_url`` and only carries an overlay-free note.
    env = Environment(
        id="lib-env",
        name="Library Env",
        variables={"note": "from-workspace"},
    )
    registry = MCPServerRegistry(
        environment_lookup=lambda env_id: env if env_id == "lib-env" else None,
        library_service=service,
    )
    config = _ordinary_library_config(
        instance_id="ordinary-lib-refresh",
        port=port,
        selection=selection,
        environment_id="lib-env",
    )
    registry.upsert(config)

    try:
        registry.start("ordinary-lib-refresh")
        wait_for_port("127.0.0.1", port)
        assert registry.is_running("ordinary-lib-refresh")

        env.variables["note"] = "updated-workspace"
        registry.refresh_environment("lib-env")

        expected = LibraryRuntimeResolver(
            library_service=service,
            environment_lookup=lambda env_id: env if env_id == "lib-env" else None,
        ).resolve(
            selection,
            environment_id="lib-env",
            candidate_overlay=None,
        )

        manager = registry.manager_for("ordinary-lib-refresh")
        vars_snapshot = manager._variable_supplier()
        assert vars_snapshot.get("note") == "updated-workspace"
        assert vars_snapshot.get("base_url") == expected.environment.get("base_url")
        assert vars_snapshot.get("base_url") == "https://api.example.com"
        assert dict(vars_snapshot) == dict(expected.environment)
    finally:
        registry.stop_all()


# ==============================================================================
# Regression guard — workspace semantics unchanged
# ==============================================================================


def test_workspace_row_reconcile_and_refresh_unchanged(tmp_path: Path) -> None:
    """Workspace rows still stop on missing collection_id and refresh with raw env vars."""
    ws_coll = _make_workspace_collection("ws-col-lib-lifecycle", "Workspace Tool")
    ws_env = Environment(
        id="ws-env-lib-lifecycle",
        variables={"key": "ws-val", "only_workspace": "present"},
    )
    collections_map = {ws_coll.id: ws_coll}
    environments_map = {ws_env.id: ws_env}

    registry = MCPServerRegistry(
        collection_lookup=collections_map.get,
        environment_lookup=environments_map.get,
    )

    port = free_port()
    ws_cfg = McpServerConfiguration(
        id="ws-srv-lib-lifecycle",
        port=port,
        collection_id=ws_coll.id,
        environment_id=ws_env.id,
        bundled_library=False,
        enabled=True,
    )
    registry.upsert(ws_cfg)

    try:
        registry.start("ws-srv-lib-lifecycle")
        wait_for_port("127.0.0.1", port)
        assert registry.is_running("ws-srv-lib-lifecycle")

        ws_env.variables["key"] = "ws-updated"
        registry.refresh_environment("ws-env-lib-lifecycle")
        manager = registry.manager_for("ws-srv-lib-lifecycle")
        vars_snapshot = manager._variable_supplier()
        assert vars_snapshot == {"key": "ws-updated", "only_workspace": "present"}

        changed = registry.reconcile_references(
            valid_collection_ids=set(),
            valid_environment_ids={ws_env.id},
        )
        assert changed is True
        assert not registry.is_running("ws-srv-lib-lifecycle")
        status = registry.status("ws-srv-lib-lifecycle")
        assert status.state == "failed"
        assert "missing collection" in status.message
    finally:
        registry.stop_all()


# ==============================================================================
# Observability — structured logs for ordinary library lifecycle (Step 6)
# ==============================================================================


def test_ordinary_library_lifecycle_observability_and_logging(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Refresh and collection-miss reconcile emit structured registry events."""
    service, selection = _create_test_library(tmp_path)
    port = free_port()
    env = Environment(
        id="lib-env-obs",
        name="Library Env",
        variables={"note": "workspace-only"},
    )
    registry = MCPServerRegistry(
        environment_lookup=lambda env_id: env if env_id == "lib-env-obs" else None,
        library_service=service,
    )
    config = _ordinary_library_config(
        instance_id="ordinary-lib-obs",
        port=port,
        selection=selection,
        environment_id="lib-env-obs",
    )
    registry.upsert(config)

    try:
        registry.start("ordinary-lib-obs")
        wait_for_port("127.0.0.1", port)
        assert registry.is_running("ordinary-lib-obs")

        caplog.clear()
        with caplog.at_level(logging.DEBUG, logger="pypost.core.mcp_server_registry"):
            env.variables["note"] = "obs-updated"
            registry.refresh_environment("lib-env-obs")
            assert "mcp_registry_refresh_library_environment" in caplog.text
            assert "instance_id=ordinary-lib-obs" in caplog.text
            assert f"library_id={selection['library_id']}" in caplog.text
            assert "bundled_library=False" in caplog.text
            assert "https://api.example.com" not in caplog.text
            assert "obs-updated" not in caplog.text

        connection = service.get_connection(selection["library_id"])
        assert connection is not None
        collection_path = Path(connection.local_path) / selection["path"]
        collection_path.unlink()

        caplog.clear()
        with caplog.at_level(logging.DEBUG, logger="pypost.core.mcp_server_registry"):
            changed = registry.reconcile_references(
                valid_collection_ids=set(),
                valid_environment_ids={"lib-env-obs"},
            )
            assert changed is True
            assert "mcp_registry_ordinary_library_collection_unresolved" in caplog.text
            assert "mcp_registry_stop_requested" in caplog.text
            assert (
                "mcp_registry_status instance_id=ordinary-lib-obs state=failed"
                in caplog.text
            )
            status = registry.status("ordinary-lib-obs")
            assert status.state == "failed"
            assert "library" in status.message.lower()
            assert "collection" in status.message.lower()
    finally:
        registry.stop_all()
