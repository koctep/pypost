"""Comprehensive tests for modernized examples collection library and legacy fixtures (PYPOST-1224)."""
from __future__ import annotations

from pathlib import Path
import pytest

from pypost.core.library_manifest import (
    find_and_read_manifest,
    read_library_manifest,
    validate_manifest_collections,
)
from pypost.core.collection_serializer import read_collection_file
from pypost.models.library_manifest import LibraryManifest
from pypost.models.models import Collection

pytestmark = pytest.mark.timeout(30)


class TestModernizedExamplesLibrary:
    def test_examples_manifest_discovery_and_structure(self):
        manifest, path = find_and_read_manifest(Path("examples"))
        assert isinstance(manifest, LibraryManifest)
        assert manifest.id == "pypost-examples"
        assert manifest.name == "PyPost Official Examples"
        assert manifest.version == "2.0.0"
        assert "collections/jira_mcp.json" in manifest.collections
        assert "collections/mcp.json" in manifest.collections

        # Variables schema
        var_names = [v.name for v in manifest.variables]
        assert "jira_base_url" in var_names
        assert "jira_project_key" in var_names
        assert "jira_credentials" in var_names

        # Secret variable flags
        creds_var = next(v for v in manifest.variables if v.name == "jira_credentials")
        assert creds_var.secret is True

        # Presets
        assert "jira_cloud" in manifest.presets

    def test_examples_collections_load_as_collections(self):
        jira_coll_path = Path("examples/collections/jira_mcp.json")
        coll = read_collection_file(jira_coll_path)
        assert isinstance(coll, Collection)
        assert coll.name == "Jira Cloud MCP"
        assert len(coll.requests) == 23
        assert len(coll.variables) >= 3

        mcp_coll_path = Path("examples/collections/mcp.json")
        mcp_coll = read_collection_file(mcp_coll_path)
        assert isinstance(mcp_coll, Collection)
        assert mcp_coll.name == "MCP"
        assert len(mcp_coll.requests) == 3


class TestLegacyFixturesRegression:
    def test_legacy_fixtures_exist(self):
        fixture_dir = Path("tests/fixtures/legacy_collections")
        assert (fixture_dir / "legacy_jira_mcp_v1.json").is_file()
        assert (fixture_dir / "legacy_jira_cloud_env_v1.json").is_file()
        assert (fixture_dir / "legacy_mcp_v1.json").is_file()
        assert (fixture_dir / "legacy_gurushots_v1.json").is_file()

    def test_legacy_collections_import_compatibility(self):
        fixture_dir = Path("tests/fixtures/legacy_collections")
        for filename in ["legacy_jira_mcp_v1.json", "legacy_mcp_v1.json", "legacy_gurushots_v1.json"]:
            path = fixture_dir / filename
            coll = read_collection_file(path)
            assert isinstance(coll, Collection)
            assert coll.name
            assert len(coll.requests) > 0

    def test_legacy_environments_compatibility(self):
        fixture_dir = Path("tests/fixtures/legacy_collections")
        env_file = fixture_dir / "legacy_jira_cloud_env_v1.json"
        assert env_file.is_file()
        import json
        data = json.loads(env_file.read_text(encoding="utf-8"))
        assert isinstance(data, list)
        assert data[0]["name"] == "Jira Cloud MCP"
        assert "jira_credentials" in data[0]["variables"]
