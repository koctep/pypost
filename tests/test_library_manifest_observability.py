"""Observability and structured logging verification tests (PYPOST-1221).

Verifies that structured logs, provenance counts, diagnostics, and secret-safe
logging contracts are satisfied across:
- pypost.core.library_manifest
- pypost.core.local_overlay_manager
- pypost.core.variable_resolver
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from pypost.core.library_manifest import (
    deserialize_manifest_from_dict,
    deserialize_manifest_from_json,
    deserialize_manifest_from_yaml,
    find_and_read_manifest,
    read_manifest_file,
    validate_manifest_collections,
    write_manifest_file,
)
from pypost.core.local_overlay_manager import LocalOverlayManager
from pypost.core.variable_resolver import (
    LibraryVariableResolver,
    resolve_detailed_variables,
    resolve_effective_variables,
)
from pypost.models.collection_variable import CollectionVariable
from pypost.models.library_manifest import (
    LibraryManifest,
    LocalLibraryOverlay,
    ManifestDiagnosticError,
)

pytestmark = pytest.mark.timeout(30)


# ============================================================================
# 1. Library Manifest Observability Tests
# ============================================================================


def test_manifest_deserialization_and_read_logging(caplog, tmp_path):
    """Manifest parse and read emit structured info/debug logs."""
    manifest_data = {
        "id": "lib-obs-test",
        "name": "Observability Test Lib",
        "collections": ["col1.yaml"],
        "variables": [
            {"name": "host", "type": "string", "default": "http://api.com"},
        ],
    }

    with caplog.at_level(logging.DEBUG, logger="pypost.core.library_manifest"):
        manifest = deserialize_manifest_from_dict(manifest_data)
        assert manifest.id == "lib-obs-test"

    assert any("manifest_deserialized_dict" in r.message for r in caplog.records)

    # Test file write and read logging
    manifest_file = tmp_path / "pypost-library.yaml"
    with caplog.at_level(logging.INFO, logger="pypost.core.library_manifest"):
        write_manifest_file(manifest, manifest_file, format="yaml")
        loaded = read_manifest_file(manifest_file)
        assert loaded.id == "lib-obs-test"

    assert any("manifest_file_written" in r.message for r in caplog.records)
    assert any("manifest_file_read" in r.message for r in caplog.records)


def test_manifest_discovery_and_collection_validation_logging(caplog, tmp_path):
    """Manifest discovery and collection path validation emit structured logs."""
    manifest_file = tmp_path / "pypost-library.yaml"
    manifest = LibraryManifest(
        id="lib-disc-test",
        name="Discovery Test",
        collections=["missing_col.yaml"],
    )
    write_manifest_file(manifest, manifest_file)

    with caplog.at_level(logging.DEBUG, logger="pypost.core.library_manifest"):
        disc_manifest, path = find_and_read_manifest(tmp_path)
        assert disc_manifest.id == "lib-disc-test"
        assert path == manifest_file

    assert any("manifest_discovered" in r.message for r in caplog.records)

    with caplog.at_level(logging.WARNING, logger="pypost.core.library_manifest"):
        missing = validate_manifest_collections(disc_manifest, manifest_dir=tmp_path)
        assert "missing_col.yaml" in missing

    assert any("manifest_collections_validation_failed" in r.message for r in caplog.records)


def test_manifest_parse_errors_logging(caplog, tmp_path):
    """Invalid syntax or root schema emits structured warnings with context."""
    with caplog.at_level(logging.WARNING, logger="pypost.core.library_manifest"):
        with pytest.raises(ManifestDiagnosticError):
            deserialize_manifest_from_yaml("id: [unclosed")

    assert any("manifest_yaml_parse_failed" in r.message for r in caplog.records)

    with caplog.at_level(logging.WARNING, logger="pypost.core.library_manifest"):
        with pytest.raises(ManifestDiagnosticError):
            deserialize_manifest_from_json("{invalid json")

    assert any("manifest_json_parse_failed" in r.message for r in caplog.records)


# ============================================================================
# 2. Local Overlay Manager Observability Tests (Secrets Masked)
# ============================================================================


def test_local_overlay_manager_logging_and_secret_safety(caplog, tmp_path):
    """LocalOverlayManager logs overlay operations without exposing secret values."""
    secret_value = "super_secret_token_never_log_this_xyz999"
    mgr = LocalOverlayManager(base_dir=tmp_path / "overlays")

    with caplog.at_level(logging.DEBUG, logger="pypost.core.local_overlay_manager"):
        # Initial missing overlay
        mgr.get_overlay("lib-secret-test")

        # Set secret and override
        mgr.set_secret("lib-secret-test", "api_token", secret_value)
        mgr.set_override("lib-secret-test", "timeout", 10)
        mgr.set_active_profile("lib-secret-test", "staging")

        # Reload overlay
        mgr.get_overlay("lib-secret-test")

        # Remove and delete
        mgr.remove_secret("lib-secret-test", "api_token")
        mgr.delete_overlay("lib-secret-test")

    # Verify structured events are logged
    assert any("overlay_not_found" in r.message for r in caplog.records)
    assert any("overlay_secret_updated" in r.message for r in caplog.records)
    assert any("overlay_override_updated" in r.message for r in caplog.records)
    assert any("overlay_saved" in r.message for r in caplog.records)
    assert any("overlay_loaded" in r.message for r in caplog.records)
    assert any("overlay_secret_removed" in r.message for r in caplog.records)
    assert any("overlay_deleted" in r.message for r in caplog.records)

    # CRITICAL SECURITY CHECK: secret value must NEVER be present in any log record!
    for record in caplog.records:
        assert secret_value not in record.message


# ============================================================================
# 3. Variable Resolver Observability & Provenance Breakdown Tests
# ============================================================================


def test_variable_resolver_logging_and_provenance_counts(caplog):
    """Variable resolver logs provenance breakdown counts and masks secret errors."""
    secret_value = "my_secret_token_12345"

    manifest = LibraryManifest(
        id="lib-obs-resolver",
        name="Resolver Observability",
        collections=["col.yaml"],
        variables=[
            CollectionVariable(name="host", type="string", default="http://default.com"),
            CollectionVariable(name="secret_key", type="string", required=True, secret=True),
            CollectionVariable(name="opt_num", type="integer", default=10),
            CollectionVariable(name="missing_var", type="string", required=True),
        ],
        presets={
            "prod": {"host": "https://prod.com"},
        },
    )

    overlay = LocalLibraryOverlay(
        library_id="lib-obs-resolver",
        active_profile="prod",
        secrets={"secret_key": secret_value},
        overrides={"opt_num": 20},
    )

    resolver = LibraryVariableResolver()

    with caplog.at_level(logging.DEBUG, logger="pypost.core.variable_resolver"):
        result = resolver.resolve(manifest=manifest, overlay=overlay)

    # Check that provenance counts and events were logged
    assert any("variable_resolution_completed" in r.message for r in caplog.records)
    assert any("variable_resolution_missing_required" in r.message for r in caplog.records)

    # CRITICAL SECURITY CHECK: secret value must NEVER appear in logs
    for record in caplog.records:
        assert secret_value not in record.message

    # Test detailed resolution logging
    with caplog.at_level(logging.DEBUG, logger="pypost.core.variable_resolver"):
        detailed = resolve_detailed_variables(manifest=manifest, overlay=overlay)
        assert "secret_key" in detailed
        assert detailed["secret_key"].is_secret is True

    assert any("variable_resolution_detailed_completed" in r.message for r in caplog.records)


def test_variable_resolver_masks_secret_type_validation_errors(caplog):
    """Type mismatch on a secret variable masks the value in error message and logs."""
    secret_val = "bad_secret_val_must_be_redacted"
    manifest = LibraryManifest(
        id="lib-secret-type-fail",
        name="Secret Type Fail",
        collections=["col.yaml"],
        variables=[
            CollectionVariable(name="secret_port", type="integer", secret=True),
        ],
    )
    overlay = LocalLibraryOverlay(
        library_id="lib-secret-type-fail",
        secrets={"secret_port": secret_val},
    )

    resolver = LibraryVariableResolver()
    with caplog.at_level(logging.WARNING, logger="pypost.core.variable_resolver"):
        result = resolver.resolve(manifest=manifest, overlay=overlay)

    assert result.is_valid is False
    assert any("Variable 'secret_port' value [REDACTED]" in err for err in result.errors)
    for record in caplog.records:
        assert secret_val not in record.message
