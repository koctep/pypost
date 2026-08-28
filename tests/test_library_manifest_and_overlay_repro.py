"""Red failing repro tests for Library Manifest and Local Overlay Manager (PYPOST-1221).

Tests the target contract before Step 4 implementation:
- LibraryManifest model, collection entries, and schema validation
- Multi-format manifest parsing (YAML and JSON) with path/file auto-discovery
- Manifest diagnostic error reporting with structured context
- LocalOverlayManager isolated storage, permissions (0o600/0o700), atomic writes, and CRUD
- 3-tier effective variable resolution: Layer 1 (defaults) -> Layer 2 (profile)
  -> Layer 3 (local overlay)
- Required variable & secret enforcement and missing value diagnostics
- Origin provenance tracking across layers
"""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from pypost.core.library_manifest import (
    deserialize_manifest_from_dict,
    deserialize_manifest_from_json,
    deserialize_manifest_from_yaml,
    find_and_read_manifest,
    read_manifest_file,
    serialize_manifest_to_json,
    serialize_manifest_to_yaml,
    validate_manifest_collections,
)
from pypost.core.local_overlay_manager import LocalOverlayManager
from pypost.core.variable_resolver import LibraryVariableResolver
from pypost.models.collection_variable import CollectionVariable
from pypost.models.library_manifest import (
    LibraryCollectionEntry,
    LibraryEnvironmentEntry,
    LibraryManifest,
    LocalLibraryOverlay,
    ManifestDiagnosticError,
    VariableProvenance,
    VariableResolutionContext,
    VariableResolutionResult,
)
from pypost.models.models import Collection

pytestmark = pytest.mark.timeout(30)


# ============================================================================
# 1. LibraryManifest Model & Schema Validation Tests
# ============================================================================


def test_library_manifest_valid_initialization():
    """Verify LibraryManifest instantiation with standard metadata,
    collections, variables, and presets.
    """
    manifest = LibraryManifest(
        id="lib-core-payments",
        name="Payments Core Library",
        version="1.2.0",
        description="Core API collections for payment processing and billing.",
        collections=["collections/billing.yaml", "collections/customers.yaml"],
        variables=[
            CollectionVariable(
                name="base_url",
                type="string",
                default="https://api.payments.example.com",
                description="Gateway URL",
                required=True,
                secret=False,
            ),
            CollectionVariable(
                name="api_key",
                type="string",
                default=None,
                description="Secret API key",
                required=True,
                secret=True,
            ),
            CollectionVariable(
                name="timeout",
                type="integer",
                default=30,
                description="Timeout in seconds",
                required=False,
                secret=False,
            ),
        ],
        presets={
            "local": {
                "base_url": "http://localhost:8080",
                "timeout": 5,
            },
            "staging": {
                "base_url": "https://staging.payments.example.com",
                "timeout": 15,
            },
        },
    )

    assert manifest.id == "lib-core-payments"
    assert manifest.name == "Payments Core Library"
    assert manifest.version == "1.2.0"
    assert manifest.description == "Core API collections for payment processing and billing."
    assert manifest.collections == ["collections/billing.yaml", "collections/customers.yaml"]
    assert len(manifest.variables) == 3
    assert manifest.variables[0].name == "base_url"
    assert manifest.variables[1].secret is True
    assert manifest.presets["local"]["timeout"] == 5


def test_library_manifest_rejects_empty_id_or_name():
    """Manifest requires non-empty id and non-empty name."""
    with pytest.raises((ValueError, ValidationError)):
        LibraryManifest(id="", name="Valid Name", collections=["col1.yaml"])

    with pytest.raises((ValueError, ValidationError)):
        LibraryManifest(id="   ", name="Valid Name", collections=["col1.yaml"])

    with pytest.raises((ValueError, ValidationError)):
        LibraryManifest(id="valid-id", name="", collections=["col1.yaml"])

    with pytest.raises((ValueError, ValidationError)):
        LibraryManifest(id="valid-id", name="   ", collections=["col1.yaml"])


def test_library_manifest_rejects_empty_collections():
    """Manifest must declare at least one collection file."""
    with pytest.raises((ValueError, ValidationError)):
        LibraryManifest(id="valid-id", name="Valid Name", collections=[])

    with pytest.raises((ValueError, ValidationError)):
        LibraryManifest(id="valid-id", name="Valid Name", collections=["   ", ""])


def test_library_collection_entry_and_environment_entry_models():
    """Value object models for collection references and preset environments."""
    entry = LibraryCollectionEntry(
        path="collections/users.yaml",
        name="Users Collection",
        description="Endpoints for user management",
    )
    assert entry.path == "collections/users.yaml"
    assert entry.name == "Users Collection"
    assert entry.description == "Endpoints for user management"

    with pytest.raises((ValueError, ValidationError)):
        LibraryCollectionEntry(path="")

    env = LibraryEnvironmentEntry(
        name="staging",
        description="Staging cluster",
        variables={"base_url": "https://stage.api.com", "debug": True},
    )
    assert env.name == "staging"
    assert env.variables["debug"] is True


# ============================================================================
# 2. Manifest Serialization & Multi-Format Parsing Tests
# ============================================================================


def test_yaml_manifest_round_trip():
    """Verify YAML manifest serialization and deserialization fidelity."""
    original = LibraryManifest(
        id="lib-inventory-v1",
        name="Inventory Management Library",
        version="2.0.1",
        description="Warehouse and inventory microservices.",
        collections=["collections/stock.yaml", "collections/warehouses.json"],
        variables=[
            CollectionVariable(
                name="host",
                type="string",
                default="https://inv.example.com",
                required=True,
            ),
            CollectionVariable(
                name="secret_token",
                type="string",
                default=None,
                required=True,
                secret=True,
            ),
        ],
        presets={
            "dev": {"host": "http://127.0.0.1:8000"},
            "prod": {"host": "https://inv.example.com"},
        },
    )

    yaml_str = serialize_manifest_to_yaml(original)
    assert isinstance(yaml_str, str)
    assert "lib-inventory-v1" in yaml_str
    assert "Inventory Management Library" in yaml_str
    assert "collections/stock.yaml" in yaml_str

    deserialized = deserialize_manifest_from_yaml(yaml_str)
    assert deserialized.id == original.id
    assert deserialized.name == original.name
    assert deserialized.version == original.version
    assert deserialized.description == original.description
    assert deserialized.collections == original.collections
    assert len(deserialized.variables) == len(original.variables)
    assert deserialized.variables[0].name == original.variables[0].name
    assert deserialized.variables[1].secret is True
    assert deserialized.presets == original.presets


def test_json_manifest_round_trip():
    """Verify JSON manifest serialization and deserialization fidelity."""
    original = LibraryManifest(
        id="lib-auth-v2",
        name="OAuth2 & SSO Library",
        version="1.0.0",
        collections=["collections/oauth.json"],
        variables=[
            CollectionVariable(name="client_id", type="string", default="client-123"),
            CollectionVariable(name="client_secret", type="string", secret=True, required=True),
        ],
        presets={"sandbox": {"client_id": "sandbox-client"}},
    )

    json_str = serialize_manifest_to_json(original, indent=2)
    assert isinstance(json_str, str)
    deserialized = deserialize_manifest_from_json(json_str)

    assert deserialized.id == original.id
    assert deserialized.name == original.name
    assert deserialized.collections == original.collections
    assert len(deserialized.variables) == 2
    assert deserialized.presets["sandbox"]["client_id"] == "sandbox-client"


def test_find_and_read_manifest_in_directory(tmp_path):
    """Auto-detect pypost-library.yaml or pypost-library.json in a folder."""
    # 1. Test YAML auto-discovery
    yaml_dir = tmp_path / "yaml_lib"
    yaml_dir.mkdir()
    manifest_yaml = yaml_dir / "pypost-library.yaml"
    manifest_yaml.write_text(
        """
id: lib-yaml-auto
name: YAML Auto Discovered
collections:
  - collections/sample.yaml
""",
        encoding="utf-8",
    )

    manifest, path = find_and_read_manifest(yaml_dir)
    assert manifest.id == "lib-yaml-auto"
    assert manifest.name == "YAML Auto Discovered"
    assert path == manifest_yaml

    # 2. Test JSON auto-discovery
    json_dir = tmp_path / "json_lib"
    json_dir.mkdir()
    manifest_json = json_dir / "pypost-library.json"
    manifest_json.write_text(
        json.dumps(
            {
                "id": "lib-json-auto",
                "name": "JSON Auto Discovered",
                "collections": ["collections/sample.json"],
            }
        ),
        encoding="utf-8",
    )

    manifest_j, path_j = find_and_read_manifest(json_dir)
    assert manifest_j.id == "lib-json-auto"
    assert path_j == manifest_json


def test_manifest_diagnostic_errors_on_invalid_syntax(tmp_path):
    """Malformed YAML/JSON raises ManifestDiagnosticError with file path and message context."""
    bad_yaml = tmp_path / "pypost-library.yaml"
    bad_yaml.write_text("id: lib-bad\nname: [unclosed bracket", encoding="utf-8")

    with pytest.raises(ManifestDiagnosticError) as exc_info:
        read_manifest_file(bad_yaml)

    err = exc_info.value
    assert err.code is not None
    assert str(bad_yaml) in str(err) or err.path == bad_yaml


def test_validate_manifest_collections_on_disk(tmp_path):
    """validate_manifest_collections identifies missing collection files."""
    lib_dir = tmp_path / "my_library"
    col_dir = lib_dir / "collections"
    col_dir.mkdir(parents=True)

    # Create one collection file on disk
    (col_dir / "billing.yaml").write_text("name: Billing API\nrequests: []\n", encoding="utf-8")

    manifest = LibraryManifest(
        id="lib-validate",
        name="Validation Library",
        collections=["collections/billing.yaml", "collections/missing_col.yaml"],
    )

    missing = validate_manifest_collections(manifest, manifest_dir=lib_dir)
    assert "collections/missing_col.yaml" in missing
    assert "collections/billing.yaml" not in missing


# ============================================================================
# 3. LocalOverlayManager CRUD & Security Isolation Tests
# ============================================================================


def test_local_overlay_manager_crud_operations(tmp_path):
    """LocalOverlayManager can create, load, update secrets/overrides, and delete overlays."""
    overlay_dir = tmp_path / "overlay_store"
    mgr = LocalOverlayManager(base_dir=overlay_dir)

    library_id = "lib-payments-prod"

    # 1. Initial get returns empty overlay with proper library_id
    initial_overlay = mgr.get_overlay(library_id)
    assert initial_overlay.library_id == library_id
    assert initial_overlay.secrets == {}
    assert initial_overlay.overrides == {}
    assert initial_overlay.active_profile is None

    # 2. Set active profile
    mgr.set_active_profile(library_id, "staging")

    # 3. Set secret
    mgr.set_secret(library_id, "api_key", "sk_live_secret_value_123")

    # 4. Set override
    mgr.set_override(library_id, "timeout", 10)
    mgr.set_override(library_id, "base_url", "http://internal-staging.local")

    # 5. Reload overlay and verify persistence
    loaded = mgr.get_overlay(library_id)
    assert loaded.library_id == library_id
    assert loaded.active_profile == "staging"
    assert loaded.secrets["api_key"] == "sk_live_secret_value_123"
    assert loaded.overrides["timeout"] == 10
    assert loaded.overrides["base_url"] == "http://internal-staging.local"

    # 6. Remove secret and override
    mgr.remove_secret(library_id, "api_key")
    mgr.remove_override(library_id, "timeout")

    updated = mgr.get_overlay(library_id)
    assert "api_key" not in updated.secrets
    assert "timeout" not in updated.overrides
    assert updated.overrides["base_url"] == "http://internal-staging.local"

    # 7. List overlays
    overlays = mgr.list_library_overlays()
    assert library_id in overlays

    # 8. Delete overlay
    deleted = mgr.delete_overlay(library_id)
    assert deleted is True
    assert library_id not in mgr.list_library_overlays()


def test_local_overlay_manager_file_and_dir_permissions(tmp_path):
    """LocalOverlayManager enforces 0o700 directory permissions and 0o600 file permissions."""
    overlay_dir = tmp_path / "secure_overlays"
    mgr = LocalOverlayManager(base_dir=overlay_dir)

    library_id = "lib-security-test"
    mgr.set_secret(library_id, "token", "super_secret_token")

    expected_file = overlay_dir / library_id / "overlay.json"
    assert expected_file.exists()

    # Verify POSIX permissions on non-Windows platforms
    if os.name == "posix":
        dir_stat = os.stat(overlay_dir / library_id)
        dir_mode = stat.S_IMODE(dir_stat.st_mode)
        assert dir_mode == 0o700, f"Directory mode should be 0o700, got {oct(dir_mode)}"

        file_stat = os.stat(expected_file)
        file_mode = stat.S_IMODE(file_stat.st_mode)
        assert file_mode == 0o600, f"File mode should be 0o600, got {oct(file_mode)}"


def test_local_overlay_manager_isolated_from_workspace(tmp_path):
    """Local overlay manager writes strictly to base_dir,
    never polluting the workspace directory.
    """
    workspace_dir = tmp_path / "workspace_repo"
    workspace_dir.mkdir()
    overlay_dir = tmp_path / "custom_pypost_data"

    mgr = LocalOverlayManager(base_dir=overlay_dir)
    mgr.set_secret("lib-isolated", "auth_token", "secret123")

    # Workspace directory must remain untouched
    workspace_files = list(workspace_dir.iterdir())
    assert len(workspace_files) == 0

    # Overlay directory must contain the data
    assert (overlay_dir / "lib-isolated" / "overlay.json").exists()


# ============================================================================
# 4. 3-Tier Layered Variable Resolution Engine Tests
# ============================================================================


def test_variable_resolution_three_tier_precedence():
    """Verify 3-tier variable precedence:
    Default (Layer 1) < Profile (Layer 2) < Overlay (Layer 3).
    """
    manifest = LibraryManifest(
        id="lib-precedence",
        name="Precedence Test Library",
        collections=["collections/api.yaml"],
        variables=[
            CollectionVariable(name="host", type="string", default="https://default.api.com"),
            CollectionVariable(name="port", type="integer", default=80),
            CollectionVariable(name="timeout", type="integer", default=30),
            CollectionVariable(name="api_token", type="string", default=None, secret=True),
            CollectionVariable(name="debug", type="boolean", default=False),
        ],
        presets={
            "staging": {
                "host": "https://staging.api.com",
                "port": 8080,
                "debug": True,
            },
            "production": {
                "host": "https://prod.api.com",
                "port": 443,
            },
        },
    )

    overlay = LocalLibraryOverlay(
        library_id="lib-precedence",
        active_profile="staging",
        secrets={
            "api_token": "secret-stage-token-xyz",
        },
        overrides={
            "port": 9000,  # Overrides preset profile port 8080
        },
    )

    resolver = LibraryVariableResolver()
    result = resolver.resolve(manifest=manifest, overlay=overlay, active_profile="staging")

    # Effective values
    assert result.variables["host"] == "https://staging.api.com"  # From Layer 2 (profile)
    assert result.variables["port"] == 9000  # From Layer 3 (override)
    assert result.variables["timeout"] == 30  # From Layer 1 (manifest default)
    assert result.variables["api_token"] == "secret-stage-token-xyz"  # From Layer 3 (secret)
    assert result.variables["debug"] is True  # From Layer 2 (profile)

    # Provenance tracking
    assert result.provenance["host"] == VariableProvenance.PROFILE
    assert result.provenance["port"] == VariableProvenance.LOCAL_OVERRIDE
    assert result.provenance["timeout"] == VariableProvenance.DEFAULT
    assert result.provenance["api_token"] == VariableProvenance.LOCAL_SECRET
    assert result.provenance["debug"] == VariableProvenance.PROFILE


def test_variable_resolution_collection_level_defaults():
    """Collection-level variable defaults are merged as Layer 1 base defaults."""
    manifest = LibraryManifest(
        id="lib-col-vars",
        name="Collection Defaults Library",
        collections=["collections/users.yaml"],
        variables=[
            CollectionVariable(name="shared_host", type="string", default="https://api.com"),
        ],
    )

    collection = Collection(
        id="col-users-1",
        name="Users Collection",
        variables=[
            CollectionVariable(name="users_endpoint", type="string", default="/v1/users"),
            CollectionVariable(name="page_size", type="integer", default=50),
        ],
    )

    resolver = LibraryVariableResolver()
    result = resolver.resolve(manifest=manifest, collection=collection)

    assert result.variables["shared_host"] == "https://api.com"
    assert result.variables["users_endpoint"] == "/v1/users"
    assert result.variables["page_size"] == 50
    assert result.provenance["users_endpoint"] == VariableProvenance.DEFAULT


def test_variable_resolution_missing_required_variables():
    """Unresolved required variables are detected and reported in missing_required list."""
    manifest = LibraryManifest(
        id="lib-required-vars",
        name="Required Vars Library",
        collections=["collections/auth.yaml"],
        variables=[
            CollectionVariable(
                name="api_host",
                type="string",
                default="https://api.com",
                required=True,
            ),
            CollectionVariable(
                name="api_key",
                type="string",
                default=None,
                required=True,
                secret=True,
            ),
            CollectionVariable(
                name="client_secret",
                type="string",
                default=None,
                required=True,
                secret=True,
            ),
            CollectionVariable(
                name="optional_token",
                type="string",
                default=None,
                required=False,
                secret=True,
            ),
        ],
    )

    # Supply only one of the required secrets in overlay
    overlay = LocalLibraryOverlay(
        library_id="lib-required-vars",
        secrets={"api_key": "provided_key"},
    )

    resolver = LibraryVariableResolver()
    result = resolver.resolve(manifest=manifest, overlay=overlay, strict_required=False)

    assert result.is_valid is False
    assert "client_secret" in result.missing_required
    assert "api_key" not in result.missing_required
    assert "optional_token" not in result.missing_required

    # In strict mode, resolve raises ManifestDiagnosticError
    with pytest.raises(ManifestDiagnosticError) as exc_info:
        resolver.resolve(manifest=manifest, overlay=overlay, strict_required=True)
    assert "client_secret" in str(exc_info.value)


def test_variable_resolution_type_validation_errors():
    """Type mismatches across preset profiles or overlay values are captured in result errors."""
    manifest = LibraryManifest(
        id="lib-type-check",
        name="Type Check Library",
        collections=["collections/service.yaml"],
        variables=[
            CollectionVariable(name="max_connections", type="integer", default=10),
            CollectionVariable(name="rate_limit", type="number", default=1.5),
        ],
        presets={
            "invalid_preset": {
                "max_connections": "not_an_int",  # Type mismatch
            }
        },
    )

    resolver = LibraryVariableResolver()
    result = resolver.resolve(manifest=manifest, active_profile="invalid_preset")

    assert result.is_valid is False
    assert len(result.errors) > 0
    assert any("max_connections" in err for err in result.errors)


def test_variable_resolution_context_object():
    """VariableResolutionContext bundles parameters and produces identical result."""
    manifest = LibraryManifest(
        id="lib-ctx-test",
        name="Context Test Library",
        collections=["collections/ctx.yaml"],
        variables=[
            CollectionVariable(
                name="service_url",
                type="string",
                default="https://default.service.com",
            ),
        ],
        presets={
            "prod": {"service_url": "https://prod.service.com"},
        },
    )

    context = VariableResolutionContext(
        manifest=manifest,
        active_profile="prod",
        strict_required=True,
    )

    resolver = LibraryVariableResolver()
    result = resolver.resolve_context(context)

    assert result.variables["service_url"] == "https://prod.service.com"
    assert result.provenance["service_url"] == VariableProvenance.PROFILE
    assert result.is_valid is True
