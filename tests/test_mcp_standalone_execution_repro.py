"""Repro test suite for standalone MCP server configuration and execution.

Jira: PYPOST-1410
Architecture: ai-tasks/PYPOST-1410/20-architecture.md
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any
import pytest
from pydantic import ValidationError
from PySide6.QtWidgets import QDialog

from pypost.core.collection_serializer import write_collection_file
from pypost.core.library_connection_store import LibraryConnectionStore
from pypost.core.library_manager_service import LibraryManagerService
from pypost.core.library_runtime_resolver import LibraryRuntimeResolver
from pypost.core.local_overlay_manager import LocalOverlayManager
from pypost.core.mcp_server_registry import MCPServerRegistry, McpServerStatus
from pypost.models.collection_variable import CollectionVariable
from pypost.models.library_manifest import LocalLibraryOverlay
from pypost.models.models import Collection, RequestData
from pypost.models.settings import McpServerConfiguration
from pypost.ui.dialogs.mcp_servers_dialog import McpServersDialog, _McpServerEditor
from tests.helpers.port_allocation import allocate_tcp_port

pytestmark = pytest.mark.timeout(30)


def _create_test_library(
    tmp_path: Path,
    variables: list[CollectionVariable] | None = None,
    presets: dict[str, dict[str, Any]] | None = None,
    requests: list[RequestData] | None = None,
) -> tuple[LibraryManagerService, dict[str, Any]]:
    """Helper to set up a valid local library with self-contained collection."""
    root = tmp_path / "standalone_library"
    (root / "collections").mkdir(parents=True, exist_ok=True)
    manifest_data = {
        "id": "standalone-lib",
        "name": "Standalone Test Library",
        "collections": ["collections/items.json"],
        "variables": [],
        "presets": {},
    }
    (root / "pypost-library.json").write_text(
        json.dumps(manifest_data), encoding="utf-8"
    )

    col_vars = (
        variables
        if variables is not None
        else [
            CollectionVariable(
                name="base_url",
                type="string",
                default="https://api.example.com",
                required=True,
            ),
        ]
    )
    col_presets = (
        presets
        if presets is not None
        else {
            "prod": {"base_url": "https://prod.example.com"},
        }
    )
    col_requests = (
        requests
        if requests is not None
        else [
            RequestData(
                id="req-1",
                name="Get Items",
                method="GET",
                url="https://{{ base_url }}/items",
                expose_as_mcp=True,
            )
        ]
    )
    collection = Collection(
        id="items-col",
        name="Items Collection",
        variables=col_vars,
        presets=col_presets,
        requests=col_requests,
    )
    write_collection_file(collection, root / "collections/items.json")

    service = LibraryManagerService(
        connection_store=LibraryConnectionStore(tmp_path / "connections.json"),
        overlay_manager=LocalOverlayManager(tmp_path / "overlays"),
    )
    service.connect_local_directory(root)

    selection = {
        "library_id": "standalone-lib",
        "manifest_id": "standalone-lib",
        "path": "collections/items.json",
        "index": 0,
        "name": "Items Collection",
    }
    return service, selection


@pytest.mark.timeout(30)
def test_mcp_server_configuration_standalone_instantiation():
    """Assert McpServerConfiguration accepts environment_id=None for library servers,

    while workspace servers still require a valid environment_id.
    """
    # 1. Standalone library MCP server can have environment_id=None
    config = McpServerConfiguration(
        id="standalone-mcp-1",
        port=1090,
        server_type="local",
        library_id="test-lib",
        manifest_id="test-manifest",
        library_collection_path="collections/test.json",
        environment_id=None,
    )
    assert config.environment_id is None

    # Serialization and round-trip validation
    dumped = config.model_dump()
    assert dumped["environment_id"] is None
    restored = McpServerConfiguration.model_validate(dumped)
    assert restored.environment_id is None

    # 2. Workspace server (collection_id set, library_id None) must still require environment_id
    with pytest.raises(ValidationError):
        McpServerConfiguration(
            id="workspace-mcp-invalid",
            port=1091,
            server_type="local",
            collection_id="workspace-col-1",
            environment_id=None,
        )


@pytest.mark.timeout(30)
def test_library_runtime_resolver_standalone_resolution(tmp_path: Path):
    """Assert LibraryRuntimeResolver resolves standalone collections with environment_id=None,

    both with active preset profiles and with default variables.
    """
    service, selection = _create_test_library(tmp_path)
    resolver = LibraryRuntimeResolver(
        library_service=service,
        environment_lookup=lambda _id: None,
    )

    # 1. Standalone resolution with active preset profile from overlay
    overlay_with_preset = LocalLibraryOverlay(
        library_id="standalone-lib",
        active_profile="prod",
    )
    result_preset = resolver.resolve(
        selection,
        environment_id=None,
        candidate_overlay=overlay_with_preset,
    )
    assert result_preset.environment["base_url"] == "https://prod.example.com"
    assert result_preset.environment_id == "prod"
    assert result_preset.overridable_keys == set()

    # 2. Standalone resolution with base collection defaults (no active preset)
    overlay_default = LocalLibraryOverlay(
        library_id="standalone-lib",
        active_profile=None,
    )
    result_default = resolver.resolve(
        selection,
        environment_id=None,
        candidate_overlay=overlay_default,
    )
    assert result_default.environment["base_url"] == "https://api.example.com"
    assert result_default.environment_id is None
    assert result_default.overridable_keys == set()


@pytest.mark.timeout(30)
def test_missing_required_variable_validation_error(tmp_path: Path):
    """Assert LibraryRuntimeResolver raises profile_invalid when required variables are missing."""
    service, selection = _create_test_library(
        tmp_path,
        variables=[
            CollectionVariable(
                name="unfulfilled_host",
                type="string",
                required=True,
                default=None,
            )
        ],
        presets={},
    )
    resolver = LibraryRuntimeResolver(
        library_service=service,
        environment_lookup=lambda _id: None,
    )
    pattern = r"profile_invalid.*required library variables are missing"
    with pytest.raises(ValueError, match=pattern):
        resolver.resolve(selection, environment_id=None)


@pytest.mark.timeout(30)
def test_mcp_server_registry_standalone_lifecycle(tmp_path: Path):
    """Assert MCPServerRegistry successfully validates, installs, and starts standalone servers."""
    service, selection = _create_test_library(tmp_path)
    port = allocate_tcp_port()

    # Construct configuration (using model_construct to test registry behavior directly)
    config = McpServerConfiguration.model_construct(
        id="standalone-daemon",
        host="127.0.0.1",
        port=port,
        server_type="local",
        library_id=selection["library_id"],
        manifest_id=selection["manifest_id"],
        library_collection_path=selection["path"],
        library_collection_index=selection["index"],
        environment_id=None,
        enabled=False,
    )

    registry = MCPServerRegistry(
        library_service=service,
        environment_lookup=lambda _id: None,
    )

    try:
        # Preflight validation must succeed with environment_id=None
        registry.validate_library_candidate(config)
        registry.upsert(config)

        # Start standalone server
        registry.start(config.id)
        assert registry.status(config.id).state == "running"
    finally:
        registry.stop_all()


@pytest.mark.timeout(30)
def test_mcp_server_registry_reconcile_references_standalone(tmp_path: Path):
    """Assert MCPServerRegistry.reconcile_references preserves standalone library servers."""
    service, selection = _create_test_library(tmp_path)
    port = allocate_tcp_port()

    config = McpServerConfiguration.model_construct(
        id="standalone-preserved",
        host="127.0.0.1",
        port=port,
        server_type="local",
        library_id=selection["library_id"],
        manifest_id=selection["manifest_id"],
        library_collection_path=selection["path"],
        library_collection_index=selection["index"],
        environment_id=None,
        enabled=False,
    )

    registry = MCPServerRegistry(
        library_service=service,
        environment_lookup=lambda _id: None,
    )
    registry.upsert(config)

    # Reconciling against empty collections and environments must not mark standalone server failed
    changed = registry.reconcile_references(
        valid_collection_ids=set(),
        valid_environment_ids=set(),
    )
    assert not changed
    assert registry.status(config.id).state != "failed"


@pytest.mark.timeout(30)
def test_mcp_server_editor_ui_standalone_workflow(qapp, tmp_path: Path):
    """Assert _McpServerEditor hides environment row and saves without environment."""
    service, selection = _create_test_library(tmp_path)

    editor = _McpServerEditor(
        collections=[],
        environments=[],
        configuration=None,
        default_environment=None,
        default_host="127.0.0.1",
        default_port=1095,
        library_service=service,
        library_selections=[selection],
    )
    try:
        # Switch source to library
        editor._collection_source.setCurrentIndex(
            editor._collection_source.findData("library")
        )

        # Environment selector and its form row label must be hidden
        assert editor._environment.isHidden()
        env_label = editor._layout.labelForField(editor._environment)
        assert env_label is None or env_label.isHidden()

        # Save dialog without workspace environments
        editor._accept_if_complete()
        assert editor.result() == QDialog.DialogCode.Accepted

        # Emitted configuration must have environment_id=None
        config = editor.configuration()
        assert config.environment_id is None
    finally:
        editor.close()


@pytest.mark.timeout(30)
def test_mcp_servers_dialog_table_renders_none_environment(qapp, tmp_path: Path):
    """Assert McpServersDialog renders '—' for standalone servers with environment_id=None."""
    service, selection = _create_test_library(tmp_path)
    config = McpServerConfiguration.model_construct(
        id="standalone-row",
        name="Standalone Row",
        host="127.0.0.1",
        port=1096,
        server_type="local",
        library_id=selection["library_id"],
        manifest_id=selection["manifest_id"],
        library_collection_path=selection["path"],
        library_collection_index=selection["index"],
        environment_id=None,
        enabled=False,
    )

    dialog = McpServersDialog(
        configurations=lambda: [config],
        status_for=lambda _id: McpServerStatus("standalone-row", "stopped"),
        save=lambda _config: None,
        remove=lambda _id: None,
        start=lambda _id: None,
        stop=lambda _id: None,
        activity=lambda _id: [],
        collections=lambda: [],
        environments=lambda: [],
        legacy_environment=lambda: None,
        legacy_host="127.0.0.1",
        legacy_port=1080,
        library_service=service,
    )
    try:
        env_col_index = dialog._COLUMNS.index("Environment")
        env_item = dialog._table.item(0, env_col_index)
        assert env_item is not None
        assert env_item.text() == "—"
    finally:
        dialog.close()


@pytest.mark.timeout(30)
def test_standalone_mcp_observability_and_logging(caplog, tmp_path: Path):
    """Assert structured logging and secret redaction for standalone MCP."""
    secret_val = "super-secret-standalone-token-999"
    service, selection = _create_test_library(
        tmp_path,
        variables=[
            CollectionVariable(name="api_token", type="string", secret=True, required=True),
            CollectionVariable(
                name="host", type="string", default="https://api.example.com", required=True
            ),
        ],
        presets={},
    )
    overlay = LocalLibraryOverlay(
        library_id="standalone-lib",
        secrets={"api_token": secret_val},
    )

    resolver = LibraryRuntimeResolver(
        library_service=service,
        environment_lookup=lambda _id: None,
    )

    with caplog.at_level(logging.DEBUG, logger="pypost.core.library_runtime_resolver"):
        inputs = resolver.resolve(selection, environment_id=None, candidate_overlay=overlay)
        assert inputs.environment["host"] == "https://api.example.com"
        assert inputs.environment_id is None

    # Assert structured log events in LibraryRuntimeResolver
    records = caplog.records
    assert any(
        "mcp_library_runtime_validation_started" in r.message
        and "environment_id=None" in r.message
        for r in records
    )
    assert any("mcp_library_profile_fallback_to_defaults" in r.message for r in records)
    assert any(
        "mcp_library_profile_resolved" in r.message
        and "environment_id=None" in r.message
        for r in records
    )
    assert any("mcp_library_secret_masking_applied" in r.message for r in records)
    assert any(
        "mcp_library_runtime_validation_completed" in r.message
        and "environment_id=None" in r.message
        for r in records
    )

    # Assert secret was NEVER leaked into logs
    for record in records:
        assert secret_val not in record.message

    # Test MCPServerRegistry startup & reconciliation logging
    port = allocate_tcp_port()
    config = McpServerConfiguration.model_construct(
        id="standalone-obs-server",
        host="127.0.0.1",
        port=port,
        server_type="local",
        library_id=selection["library_id"],
        manifest_id=selection["manifest_id"],
        library_collection_path=selection["path"],
        library_collection_index=selection["index"],
        environment_id=None,
        enabled=False,
    )
    registry = MCPServerRegistry(
        library_service=service,
        environment_lookup=lambda _id: None,
    )

    with caplog.at_level(logging.DEBUG, logger="pypost.core.mcp_server_registry"):
        registry.upsert(config)
        try:
            registry.start(config.id)
            assert any(
                "mcp_registry_start_requested" in r.message
                and "standalone=True" in r.message
                and "environment_id=None" in r.message
                for r in caplog.records
            )
            assert any(
                "mcp_registry_manager_starting" in r.message
                and "standalone=True" in r.message
                for r in caplog.records
            )

            # Reconcile references skipping environment check log
            registry.reconcile_references(
                valid_collection_ids=set(),
                valid_environment_ids=set(),
            )
            assert any(
                "mcp_registry_reconcile_standalone_library_server" in r.message
                and "skipping_environment_check=True" in r.message
                for r in caplog.records
            )
        finally:
            registry.stop_all()
