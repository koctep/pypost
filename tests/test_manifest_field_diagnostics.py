"""Tests for field-level validation diagnostics in library manifests (PYPOST-1226)."""
from __future__ import annotations

import pytest

from pypost.core.library_manifest import deserialize_manifest_from_dict
from pypost.models.library_manifest import ManifestDiagnosticError

pytestmark = pytest.mark.timeout(30)


def test_manifest_diagnostic_error_attributes():
    """ManifestDiagnosticError provides structured field and location info."""
    err = ManifestDiagnosticError(
        code="MANIFEST_VALIDATION_ERROR",
        message="Validation failed",
        field="variables[0].name",
        json_path="$.variables[0].name",
        line=10,
        column=5,
        field_errors=[
            {
                "field": "variables[0].name",
                "json_path": "$.variables[0].name",
                "message": "Field required",
                "type": "missing",
            }
        ],
    )
    assert err.field == "variables[0].name"
    assert err.json_path == "$.variables[0].name"
    assert err.line == 10
    assert err.column == 5
    assert len(err.field_errors) == 1
    assert err.field_errors[0]["json_path"] == "$.variables[0].name"

    data = err.to_dict()
    assert data["code"] == "MANIFEST_VALIDATION_ERROR"
    assert data["field"] == "variables[0].name"
    assert data["json_path"] == "$.variables[0].name"
    assert data["line"] == 10
    assert data["column"] == 5


def test_deserialize_manifest_extracts_field_level_error_for_root_field():
    """deserialize_manifest_from_dict populates field and json_path for root validation errors."""
    bad_data = {
        "id": "",  # Empty id fails validation
        "name": "Valid Name",
        "collections": ["col1.yaml"],
    }
    with pytest.raises(ManifestDiagnosticError) as exc_info:
        deserialize_manifest_from_dict(bad_data)

    err = exc_info.value
    assert err.field == "id"
    assert err.json_path == "$.id"
    assert len(err.field_errors) >= 1
    assert err.field_errors[0]["field"] == "id"
    assert err.field_errors[0]["json_path"] == "$.id"


def test_deserialize_manifest_extracts_nested_field_path():
    """deserialize_manifest_from_dict populates nested path (e.g. variables[0].name)."""
    bad_data = {
        "id": "lib-valid",
        "name": "Valid Library",
        "collections": ["col1.yaml"],
        "variables": [
            {
                "name": "",  # Invalid empty variable name
                "type": "string",
            }
        ],
    }
    with pytest.raises(ManifestDiagnosticError) as exc_info:
        deserialize_manifest_from_dict(bad_data)

    err = exc_info.value
    assert "variables" in err.field
    assert err.json_path.startswith("$.variables")
    assert len(err.field_errors) >= 1
