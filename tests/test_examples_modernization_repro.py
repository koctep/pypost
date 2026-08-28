"""Repro and regression test for modernizing examples to unified library format and legacy fixtures (PYPOST-1224)."""
from __future__ import annotations

from pathlib import Path
import pytest

pytestmark = pytest.mark.timeout(30)

from pypost.core.library_manifest import (
    read_library_manifest,
    validate_manifest_collections,
)
from pypost.models.library_manifest import LibraryManifest
from pypost.core.collection_serializer import read_collection_file


def test_examples_library_manifest_validity():
    """Verify examples/ directory contains a valid pypost-library.yaml manifest."""
    manifest_path = Path("examples/pypost-library.yaml")
    assert manifest_path.is_file(), "examples/pypost-library.yaml does not exist"

    manifest = read_library_manifest(manifest_path)
    assert isinstance(manifest, LibraryManifest)
    assert manifest.id
    assert len(manifest.collections) > 0

    # Validate that collections declared in manifest exist on disk
    missing = validate_manifest_collections(manifest, manifest_dir=Path("examples"))
    assert missing == [], f"Manifest references missing collection files: {missing}"


def test_legacy_fixtures_directory_and_loading():
    """Verify legacy test fixtures exist and load with backwards compatibility."""
    fixtures_dir = Path("tests/fixtures/legacy_collections")
    assert fixtures_dir.is_dir(), "tests/fixtures/legacy_collections/ does not exist"

    legacy_jira = fixtures_dir / "legacy_jira_mcp_v1.json"
    assert legacy_jira.is_file(), f"Missing legacy fixture: {legacy_jira}"

    coll = read_collection_file(legacy_jira)
    assert coll.name
    assert len(coll.requests) > 0
