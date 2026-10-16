"""End-to-end integration and compatibility matrix test suite (PYPOST-1412).

Asserts cross-subsystem contracts across:
1. End-to-end workflow: catalog discovery, standalone MCP server execution,
   workspace collection copying, environment variable import, and template substitution.
2. 4-quadrant compatibility matrix across legacy v1 and modern v2 manifests & collections.
3. Diagnostic safety and secret redaction across failure and error paths.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from pathlib import Path
from typing import Any, Optional
import pytest

from pypost.core.collection_serializer import read_collection_file
from pypost.core.collection_variable_import import (
    ConflictStrategy,
    ImportSummary,
    import_collection_variables_to_environment,
)
from pypost.core.library_connection_store import LibraryConnectionStore
from pypost.core.library_manager_service import LibraryManagerService
from pypost.core.library_manifest import read_manifest_file
from pypost.core.library_runtime_resolver import LibraryRuntimeResolver
from pypost.core.local_overlay_manager import LocalOverlayManager
from pypost.core.mcp_server_registry import MCPServerRegistry
from pypost.core.storage import StorageManager
from pypost.core.template_service import TemplateService
from pypost.core.variable_resolver import LibraryVariableResolver
from pypost.models.collection_variable import CollectionVariable
from pypost.models.library_manifest import LocalLibraryOverlay
from pypost.models.models import Environment
from pypost.models.settings import McpServerConfiguration
from tests.helpers.port_allocation import allocate_tcp_port

pytestmark = [pytest.mark.timeout(30)]


@dataclass
class UnifiedLifecycleResult:
    """Outcome of end-to-end multi-subsystem workflow execution."""

    status: str
    standalone_server_id: str
    standalone_status: str
    imported_summary: ImportSummary
    rendered_request_url: str
    rendered_auth_header: str
    rendered_body: str


class CollectionVariablesIntegrationHarness:
    """Encapsulates isolated filesystem, configuration stores, and service instances

    for end-to-end integration and compatibility matrix validation.
    """

    def __init__(self, tmp_path: Path):
        self.tmp_path = tmp_path
        self.libraries_dir = tmp_path / "libraries"
        self.workspace_dir = tmp_path / "workspace"
        self.overlay_dir = tmp_path / "libraries_data"
        self.libraries_dir.mkdir(parents=True, exist_ok=True)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.overlay_dir.mkdir(parents=True, exist_ok=True)

        self.storage_manager = StorageManager(data_dir=self.workspace_dir)
        self.connection_store = LibraryConnectionStore(self.tmp_path / "connections.json")
        self.overlay_manager = LocalOverlayManager(self.overlay_dir)
        self.template_service = TemplateService()
        self.library_service = LibraryManagerService(
            connection_store=self.connection_store,
            overlay_manager=self.overlay_manager,
        )
        self.runtime_resolver = LibraryRuntimeResolver(
            library_service=self.library_service,
            environment_lookup=lambda _id: None,
        )
        self.registry = MCPServerRegistry(
            library_service=self.library_service,
            environment_lookup=lambda _id: None,
            template_service=self.template_service,
        )

    def create_library(
        self,
        manifest_id: str,
        is_legacy_manifest: bool = False,
        collections_data: dict[str, dict[str, Any]] | None = None,
        manifest_variables: list[CollectionVariable] | None = None,
        manifest_presets: dict[str, dict[str, Any]] | None = None,
    ) -> Path:
        """Create library directory with catalog or legacy manifest."""
        lib_dir = self.libraries_dir / manifest_id
        lib_dir.mkdir(parents=True, exist_ok=True)
        collections_dir = lib_dir / "collections"
        collections_dir.mkdir(parents=True, exist_ok=True)

        rel_paths = []
        if collections_data:
            for filename, col_dict in collections_data.items():
                col_path = collections_dir / filename
                rel_paths.append(f"collections/{filename}")
                if "id" not in col_dict:
                    col_dict["id"] = filename.split(".")[0]
                col_path.write_text(json.dumps(col_dict, indent=2), encoding="utf-8")

        manifest_dict: dict[str, Any] = {
            "id": manifest_id,
            "name": f"Library {manifest_id}",
            "version": "1.0.0" if is_legacy_manifest else "2.0.0",
            "collections": rel_paths,
        }
        if is_legacy_manifest:
            manifest_dict["variables"] = [v.model_dump() for v in (manifest_variables or [])]
            manifest_dict["presets"] = manifest_presets or {}

        manifest_file = lib_dir / "pypost-library.json"
        manifest_file.write_text(json.dumps(manifest_dict, indent=2), encoding="utf-8")

        self.library_service.connect_local_directory(lib_dir)
        return lib_dir

    def create_workspace_environment(
        self,
        name: str = "Test Env",
        variables: dict[str, str] | None = None,
        hidden_keys: set[str] | None = None,
    ) -> Environment:
        """Create and persist an isolated workspace environment."""
        env = Environment(
            name=name,
            variables=variables or {},
            hidden_keys=hidden_keys or set(),
        )
        self.storage_manager.save_environments([env])
        return env

    def run_unified_lifecycle(
        self,
        *,
        manifest_id: str,
        collection_data: dict[str, Any],
        active_profile: str,
        overlay_secrets: dict[str, str],
        workspace_env_name: str,
        conflict_strategy: ConflictStrategy,
    ) -> Optional[UnifiedLifecycleResult]:
        """Execute full unified multi-subsystem workflow orchestration:

        catalog discovery -> standalone MCP server startup -> collection copy ->
        workspace environment import -> template substitution.
        """
        collection_id = collection_data.get("id", "collection")
        col_filename = f"{collection_id}.json"

        # 1. Connect library to library_service (via create_library)
        lib_dir = self.create_library(
            manifest_id=manifest_id,
            is_legacy_manifest=False,
            collections_data={col_filename: collection_data},
        )

        # 2. Save overlay secrets into overlay_manager
        if overlay_secrets or active_profile:
            overlay = LocalLibraryOverlay(
                library_id=manifest_id,
                active_profile=active_profile,
                secrets=dict(overlay_secrets) if overlay_secrets else {},
            )
            self.overlay_manager.save_overlay(overlay)

        # 3. Register and start standalone server in registry
        server_id = f"standalone-{manifest_id}-{collection_id}"
        config = McpServerConfiguration.model_construct(
            id=server_id,
            name=f"Standalone {collection_data.get('name', collection_id)}",
            host="127.0.0.1",
            port=allocate_tcp_port(),
            server_type="local",
            library_id=manifest_id,
            manifest_id=manifest_id,
            library_collection_path=f"collections/{col_filename}",
            library_collection_index=0,
            environment_id=None,
            enabled=True,
        )
        self.registry.validate_library_candidate(config)
        self.registry.upsert(config)
        self.registry.start(config.id)
        standalone_status = self.registry.status(config.id).state

        # 4. Import collection variables into a workspace environment
        env = self.create_workspace_environment(name=workspace_env_name)
        col_file_path = lib_dir / "collections" / col_filename
        collection = read_collection_file(col_file_path)
        summary = import_collection_variables_to_environment(
            environment=env,
            collection=collection,
            conflict_strategy=conflict_strategy,
            preset_name=active_profile,
        )

        # 5. Build context combining environment variables and template variables
        context: dict[str, Any] = dict(env.variables)

        # 6. Render request URL, headers, and body with template_service
        req = collection.requests[0] if collection.requests else None
        rendered_url = ""
        rendered_auth = ""
        rendered_body = ""
        if req is not None:
            rendered_url = self.template_service.render_string(req.url, context)
            auth_header = req.headers.get("Authorization", "")
            rendered_auth = self.template_service.render_string(auth_header, context)
            rendered_body = self.template_service.render_string(req.body, context)

        return UnifiedLifecycleResult(
            status="success",
            standalone_server_id=server_id,
            standalone_status=standalone_status,
            imported_summary=summary,
            rendered_request_url=rendered_url,
            rendered_auth_header=rendered_auth,
            rendered_body=rendered_body,
        )


@pytest.mark.timeout(30)
def test_e2e_collection_scoped_variables_lifecycle(tmp_path: Path) -> None:
    """Verify complete multi-subsystem workflow across catalog discovery, standalone MCP

    server execution, collection copying, environment variable import, and template substitution.
    """
    harness = CollectionVariablesIntegrationHarness(tmp_path)

    # 1. Create catalog-only manifest with self-contained collection
    col_dict = {
        "id": "col-auth-e2e",
        "name": "Auth Service",
        "variables": [
            {
                "name": "base_url",
                "type": "string",
                "default": "https://api.example.com",
                "required": True,
                "secret": False,
            },
            {
                "name": "client_id",
                "type": "string",
                "default": "dev-client-123",
                "required": True,
                "secret": False,
            },
            {
                "name": "client_secret",
                "type": "string",
                "default": "default-col-secret",
                "required": True,
                "secret": True,
            },
            {
                "name": "timeout_seconds",
                "type": "integer",
                "default": 10,
                "required": False,
                "secret": False,
            },
        ],
        "presets": {
            "staging": {
                "base_url": "https://staging.example.com",
                "client_id": "staging-client-456",
            },
            "prod": {
                "base_url": "https://prod.example.com",
                "client_id": "prod-client-789",
            },
        },
        "requests": [
            {
                "id": "req-login",
                "name": "OAuth Login",
                "method": "POST",
                "url": "{{ base_url }}/oauth/token",
                "headers": {
                    "X-Client-Id": "{{ client_id }}",
                    "Authorization": "Bearer {{ client_secret }}",
                },
                "body": '{"client_id": "{{ client_id }}", "timeout": {{ timeout_seconds }}}',
                "expose_as_mcp": True,
            }
        ],
    }

    try:
        # Run unified multi-subsystem lifecycle through integration harness
        result = harness.run_unified_lifecycle(
            manifest_id="auth-catalog-lib",
            collection_data=col_dict,
            active_profile="staging",
            overlay_secrets={"client_secret": "overlay-secret-xyz"},
            workspace_env_name="Dev Environment",
            conflict_strategy=ConflictStrategy.OVERWRITE,
        )

        assert result is not None, "Unified integration runner pending Step 4 implementation"
        assert result.status == "success"
        assert result.standalone_status == "running"
        assert result.rendered_request_url == "https://staging.example.com/oauth/token"
        assert result.rendered_auth_header == "Bearer default-col-secret"
        assert result.rendered_body == '{"client_id": "staging-client-456", "timeout": 10}'
    finally:
        harness.registry.stop_all()


@pytest.mark.parametrize(
    "manifest_variant,collection_variant,expected_source,expected_warnings",
    [
        ("modern_catalog", "modern_collection", "collection", False),
        ("legacy_manifest", "modern_collection", "collection_with_fallback", True),
        ("legacy_manifest", "legacy_collection", "manifest_fallback", True),
        ("modern_catalog", "legacy_collection", "empty_resolution", False),
    ],
)
@pytest.mark.timeout(30)
def test_compatibility_matrix_quadrants(
    manifest_variant: str,
    collection_variant: str,
    expected_source: str,
    expected_warnings: bool,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Validate full 4-quadrant compatibility matrix across legacy v1 and modern v2

    manifests & collections, ensuring backward-compatible precedence and deprecation notices.
    """
    caplog.set_level(logging.WARNING, logger="pypost.core.library_manifest")

    is_legacy_manifest = manifest_variant == "legacy_manifest"
    is_modern_collection = collection_variant == "modern_collection"

    manifest_vars = []
    manifest_presets = {}
    if is_legacy_manifest:
        manifest_vars = [
            CollectionVariable(
                name="api_url",
                type="string",
                default="https://legacy.manifest.com",
            ),
            CollectionVariable(
                name="legacy_fallback_key",
                type="string",
                default="fallback-manifest-value",
            ),
        ]
        manifest_presets = {
            "prod": {
                "api_url": "https://legacy.prod.com",
                "legacy_fallback_key": "prod-fallback-manifest-value",
            }
        }

    col_dict: dict[str, Any] = {
        "id": "col-matrix-test",
        "name": "Matrix Collection",
        "requests": [],
    }
    if is_modern_collection:
        col_dict["variables"] = [
            {
                "name": "api_url",
                "type": "string",
                "default": "https://collection.default.com",
            },
            {
                "name": "modern_col_key",
                "type": "string",
                "default": "modern-col-value",
            },
        ]
        col_dict["presets"] = {
            "prod": {
                "api_url": "https://collection.prod.com",
            }
        }
    else:
        col_dict["variables"] = []
        col_dict["presets"] = {}

    harness = CollectionVariablesIntegrationHarness(tmp_path)
    lib_path = harness.create_library(
        manifest_id=f"lib-{manifest_variant}-{collection_variant}",
        is_legacy_manifest=is_legacy_manifest,
        collections_data={"items.json": col_dict},
        manifest_variables=manifest_vars,
        manifest_presets=manifest_presets,
    )

    # Ingestion validation
    manifest = read_manifest_file(lib_path / "pypost-library.json")
    collection = read_collection_file(lib_path / "collections/items.json")

    # Check deprecation logs
    legacy_log_present = any(
        "legacy_manifest_variables_detected" in record.message
        for record in caplog.records
    )
    if expected_warnings:
        assert legacy_log_present, "Expected legacy_manifest_variables_detected deprecation log"
    else:
        assert not legacy_log_present, (
            "Unexpected legacy deprecation log emitted for modern catalog"
        )

    # Precedence resolution check
    resolver = LibraryVariableResolver()
    resolved = resolver.resolve(
        manifest=manifest,
        collection=collection,
        active_profile="prod",
    )

    if expected_source == "collection":
        assert resolved.variables["api_url"] == "https://collection.prod.com"
        assert resolved.variables["modern_col_key"] == "modern-col-value"
        assert "legacy_fallback_key" not in resolved.variables
    elif expected_source == "collection_with_fallback":
        # Collection wins for overlapping keys, legacy manifest serves as fallback for missing keys
        assert resolved.variables["api_url"] == "https://collection.prod.com"
        assert resolved.variables["modern_col_key"] == "modern-col-value"
        assert resolved.variables["legacy_fallback_key"] == "prod-fallback-manifest-value"
    elif expected_source == "manifest_fallback":
        # Legacy manifest handles all variables
        assert resolved.variables["api_url"] == "https://legacy.prod.com"
        assert resolved.variables["legacy_fallback_key"] == "prod-fallback-manifest-value"
    elif expected_source == "empty_resolution":
        # Neither declares variables
        assert resolved.variables == {}


@pytest.mark.timeout(30)
def test_e2e_diagnostics_and_secret_redaction(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify diagnostic error handling when required variables are unfulfilled,

    and verify that sensitive secret tokens are never exposed in plaintext error messages or logs.
    """
    secret_token_plaintext = "super_secret_diagnostic_vault_token_998877"
    harness = CollectionVariablesIntegrationHarness(tmp_path)

    col_dict = {
        "id": "col-diagnostic-test",
        "name": "Diagnostic Collection",
        "variables": [
            {
                "name": "missing_required_host",
                "type": "string",
                "required": True,
                "default": None,
                "secret": False,
            },
            {
                "name": "secret_api_key",
                "type": "string",
                "required": True,
                "default": secret_token_plaintext,
                "secret": True,
            },
        ],
        "presets": {},
        "requests": [],
    }

    lib_path = harness.create_library(
        manifest_id="lib-diagnostic",
        is_legacy_manifest=False,
        collections_data={"api.json": col_dict},
    )

    selection = {
        "library_id": "lib-diagnostic",
        "manifest_id": "lib-diagnostic",
        "path": "collections/api.json",
        "index": 0,
        "name": "Diagnostic Collection",
    }

    # 1. Resolver raises profile_invalid for missing required non-secret variable
    pattern = r"profile_invalid.*required library variables are missing"
    with caplog.at_level(logging.DEBUG):
        with pytest.raises(ValueError, match=pattern):
            harness.runtime_resolver.resolve(selection, environment_id=None)

    # 2. Secret Redaction Contract: Ensure secret_token_plaintext NEVER appears in error traces
    for record in caplog.records:
        assert secret_token_plaintext not in record.message, (
            f"Secret leaked in log message: {record.message}"
        )

    # 3. Environment Import with Secret Masking & Verification
    col = read_collection_file(lib_path / "collections/api.json")
    env = harness.create_workspace_environment(name="Secret Safety Env")
    summary = import_collection_variables_to_environment(
        environment=env,
        collection=col,
        conflict_strategy=ConflictStrategy.OVERWRITE,
    )

    assert "secret_api_key" in summary.newly_hidden_keys
    assert "secret_api_key" in env.hidden_keys
    assert env.variables["secret_api_key"] == secret_token_plaintext

    # Verify formatted import summary never displays secret plaintext
    summary_text = summary.format_summary()
    assert secret_token_plaintext not in summary_text
