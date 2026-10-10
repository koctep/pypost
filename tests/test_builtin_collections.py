"""Contract and reproduction tests for BuiltinCollectionView (PYPOST-1350)."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
import yaml

from pypost.core.builtin_collections import (
    BuiltinCollectionEntry,
    BuiltinCollectionView,
)
from pypost.core.predefined_library import PredefinedLibraryService
from pypost.models.models import Collection, Environment
from pypost.models.settings import McpServerConfiguration

pytestmark = pytest.mark.timeout(30)

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_ROOT = REPO_ROOT / "examples"


def _read_manifest_data(root: Path = EXAMPLES_ROOT) -> dict:
    manifest_path = root / "pypost-library.yaml"
    with manifest_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _assert_environment_structural_consistency(
    manifest_data: dict,
    collection_data: dict,
    env_data: dict,
) -> None:
    """Validate paired environment structure against manifest declarations.

    Does not compare environment variable values directly.
    """
    collection_vars = collection_data.get("variables", [])
    if isinstance(collection_vars, list):
        collection_var_names = {
            v["name"] if isinstance(v, dict) else v.name for v in collection_vars
        }
    else:
        collection_var_names = set()

    manifest_vars = {v["name"]: v for v in manifest_data.get("variables", [])}

    env_vars = env_data.get("variables", {})
    env_keys = set(env_vars.keys())

    # 1. Variable keys match manifest-declared variables used by the collection
    expected_keys = {
        name for name in collection_var_names if name in manifest_vars
    }
    assert (
        env_keys == expected_keys
    ), f"Environment keys {env_keys} do not match expected manifest collection keys {expected_keys}"

    # 2. Hidden keys match variables marked secret
    expected_secret_keys = {
        name
        for name in expected_keys
        if manifest_vars[name].get("secret", False)
    }
    hidden_keys = set(env_data.get("hidden_keys", []))
    assert (
        hidden_keys == expected_secret_keys
    ), f"Hidden keys {hidden_keys} do not match expected secret keys {expected_secret_keys}"

    # 3. Non-empty placeholder values for all secret keys
    for secret_key in expected_secret_keys:
        val = env_vars.get(secret_key)
        assert (
            isinstance(val, str) and len(val.strip()) > 0
        ), f"Secret key {secret_key} must have non-empty string placeholder in environment"

    # 4. Overridable keys are a subset of variable keys
    overridable_keys = set(env_data.get("mcp_overridable_keys", []))
    assert overridable_keys.issubset(
        env_keys
    ), f"Overridable keys {overridable_keys} are not a subset of env keys {env_keys}"


def test_builtin_collections_list_entries():
    """BuiltinCollectionView.list_entries() returns 3 curated entries.

    Ensures entries match builtin-collections.yaml.
    """
    view = BuiltinCollectionView()
    entries = view.list_entries()

    assert len(entries) == 3

    expected = [
        {
            "collection_path": "collections/jira_mcp.json",
            "environment_path": "environments/jira_cloud.json",
            "collection_id": "jira-cloud-mcp",
            "version": "2.0.0",
        },
        {
            "collection_path": "collections/gitlab_mcp.json",
            "environment_path": "environments/gitlab.json",
            "collection_id": "gitlab-mcp",
            "version": "1.0.0",
        },
        {
            "collection_path": "collections/github_mcp.json",
            "environment_path": "environments/github.json",
            "collection_id": "github-mcp",
            "version": "1.0.0",
        },
    ]

    for entry, exp in zip(entries, expected):
        assert isinstance(entry, BuiltinCollectionEntry)
        assert entry.collection_path == exp["collection_path"]
        assert entry.environment_path == exp["environment_path"]
        assert entry.collection_id == exp["collection_id"]
        assert entry.version == exp["version"]
        assert entry.name != ""

    paths = [e.collection_path for e in entries]
    assert "collections/mcp.json" not in paths


def test_builtin_collection_entry_selection():
    """BuiltinCollectionEntry.selection() returns library identity dictionary."""
    view = BuiltinCollectionView()
    entries = view.list_entries()
    assert len(entries) >= 1

    for entry in entries:
        selection = entry.selection()
        assert selection == {
            "library_id": "pypost-examples",
            "manifest_id": "pypost-examples",
            "path": entry.collection_path,
        }


def test_builtin_collections_load_collection_and_environment():
    """load_collection() and load_paired_environment() succeed for each entry."""
    view = BuiltinCollectionView()
    entries = view.list_entries()
    assert len(entries) == 3

    for entry in entries:
        collection = view.load_collection(entry.collection_path)
        assert isinstance(collection, Collection)
        assert collection.id == entry.collection_id
        assert len(collection.requests) > 0

        env = view.load_paired_environment(entry.collection_path)
        assert isinstance(env, Environment)
        assert env.enable_mcp is True
        assert len(env.variables) > 0


def test_builtin_collections_load_fresh():
    """Fresh loading: successive load_collection() calls do not return mutated cached objects."""
    view = BuiltinCollectionView()
    entries = view.list_entries()
    assert len(entries) >= 1

    first_entry = entries[0]
    coll_1 = view.load_collection(first_entry.collection_path)
    coll_2 = view.load_collection(first_entry.collection_path)
    assert coll_1 is not coll_2

    # Mutate coll_1 and ensure coll_2 / coll_3 are pristine
    coll_1.name = "Mutated In Memory"
    coll_3 = view.load_collection(first_entry.collection_path)
    assert coll_3.name != "Mutated In Memory"

    env_1 = view.load_paired_environment(first_entry.collection_path)
    env_2 = view.load_paired_environment(first_entry.collection_path)
    assert env_1 is not env_2
    env_1.name = "Mutated Env"
    env_3 = view.load_paired_environment(first_entry.collection_path)
    assert env_3.name != "Mutated Env"


def test_builtin_collections_is_builtin():
    """is_builtin returns True for configurations targeting built-in collections."""
    view = BuiltinCollectionView()

    config_jira = McpServerConfiguration(
        id="jira-mcp-srv",
        port=9000,
        environment_id="jira-cloud-mcp-environment",
        library_id="pypost-examples",
        manifest_id="pypost-examples",
        library_collection_path="collections/jira_mcp.json",
    )
    assert view.is_builtin(config_jira) is True

    config_test_mcp = McpServerConfiguration(
        id="test-mcp-srv",
        port=9001,
        environment_id="test-env",
        library_id="pypost-examples",
        manifest_id="pypost-examples",
        library_collection_path="collections/mcp.json",
    )
    assert view.is_builtin(config_test_mcp) is False

    config_external = McpServerConfiguration(
        id="external-srv",
        port=9002,
        environment_id="other-env",
        library_id="other-library",
        manifest_id="other-library",
        library_collection_path="collections/jira_mcp.json",
    )
    assert view.is_builtin(config_external) is False


def test_builtin_collections_invalid_view_file_graceful_handling(tmp_path: Path):
    """Non-existent or malformed view file yields empty list and diagnostic, never raises."""
    # 1. Non-existent catalog file
    service_missing = PredefinedLibraryService(root=tmp_path)
    view_missing = BuiltinCollectionView(predefined=service_missing)
    entries = view_missing.list_entries()
    assert entries == []
    assert len(view_missing.diagnostics) > 0

    # 2. Malformed catalog file in a valid library directory
    fake_lib = tmp_path / "fake_lib"
    fake_lib.mkdir()
    # Write minimum valid manifest so PredefinedLibraryService doesn't fail immediately
    manifest_file = fake_lib / "pypost-library.yaml"
    manifest_file.write_text(
        "id: pypost-examples\nschema_version: '1.0.0'\nname: Fake\n"
        "version: '1.0.0'\ncollections: []\nvariables: []\n",
        encoding="utf-8",
    )
    bad_catalog = fake_lib / BuiltinCollectionView.CATALOG_FILENAME
    bad_catalog.write_text("invalid: [broken yaml: {", encoding="utf-8")

    service_malformed = PredefinedLibraryService(root=fake_lib)
    view_malformed = BuiltinCollectionView(predefined=service_malformed)
    entries_malformed = view_malformed.list_entries()
    assert entries_malformed == []
    assert len(view_malformed.diagnostics) > 0


def test_builtin_collections_non_manifest_entry_rejected(tmp_path: Path):
    """Entries with collection paths not in manifest are rejected with diagnostic."""
    lib_dir = tmp_path / "lib"
    lib_dir.mkdir()
    (lib_dir / "collections").mkdir()
    (lib_dir / "environments").mkdir()

    manifest_file = lib_dir / "pypost-library.yaml"
    manifest_file.write_text(
        "id: pypost-examples\nschema_version: '1.0.0'\nname: Fake\n"
        "version: '1.0.0'\ncollections: []\nvariables: []\n",
        encoding="utf-8",
    )
    catalog_file = lib_dir / BuiltinCollectionView.CATALOG_FILENAME
    catalog_content = {
        "version": "1.0.0",
        "entries": [
            {
                "collection": "collections/undeclared.json",
                "environment": "environments/env.json",
                "name": "Undeclared",
            }
        ],
    }
    catalog_file.write_text(yaml.dump(catalog_content), encoding="utf-8")

    service = PredefinedLibraryService(root=lib_dir)
    view = BuiltinCollectionView(predefined=service)
    entries = view.list_entries()
    assert entries == []
    assert any(
        "undeclared" in diag.lower() or "manifest" in diag.lower()
        for diag in view.diagnostics
    )


def test_builtin_collections_logging_and_diagnostics(caplog: pytest.LogCaptureFixture):
    """Verify structured logging emitted for discovery, loading, and diagnostics."""
    caplog.set_level("DEBUG", logger="pypost.core.builtin_collections")
    view = BuiltinCollectionView()
    entries = view.list_entries()

    assert len(entries) == 3
    assert len(view.diagnostics) == 0

    # Verify debug log for each loaded entry
    debug_records = [r for r in caplog.records if r.levelname == "DEBUG"]
    assert any("builtin_collection_entry_loaded" in r.message for r in debug_records)

    # Verify info log for completion
    info_records = [r for r in caplog.records if r.levelname == "INFO"]
    assert any("builtin_collections_list_completed" in r.message for r in info_records)

    # Verify warning log when catalog file is missing
    caplog.clear()
    broken_view = BuiltinCollectionView(predefined=PredefinedLibraryService(root=Path("/nonexistent")))
    broken_entries = broken_view.list_entries()
    assert broken_entries == []
    assert len(broken_view.diagnostics) > 0
    warning_records = [r for r in caplog.records if r.levelname == "WARNING"]
    assert any("builtin_collections_unavailable" in r.message for r in warning_records)


def test_paired_environments_structural_consistency():
    """Structural consistency for paired environments.

    Checks keys, hidden secrets, non-empty values, and overridables.
    """
    manifest_data = _read_manifest_data()

    paired_checks = [
        ("collections/jira_mcp.json", "environments/jira_cloud.json"),
        ("collections/gitlab_mcp.json", "environments/gitlab.json"),
        ("collections/github_mcp.json", "environments/github.json"),
    ]

    for coll_rel, env_rel in paired_checks:
        coll_path = EXAMPLES_ROOT / coll_rel
        env_path = EXAMPLES_ROOT / env_rel

        with coll_path.open("r", encoding="utf-8") as f:
            coll_data = json.load(f)

        with env_path.open("r", encoding="utf-8") as f:
            env_content = json.load(f)
            env_data = env_content[0] if isinstance(env_content, list) else env_content

        _assert_environment_structural_consistency(
            manifest_data, coll_data, env_data
        )


def test_paired_environments_seeded_defect_missing_key():
    """Seeded defect test: missing variable key in environment fails structural assertion."""
    manifest_data = _read_manifest_data()
    coll_path = EXAMPLES_ROOT / "collections" / "jira_mcp.json"
    env_path = EXAMPLES_ROOT / "environments" / "jira_cloud.json"

    with coll_path.open("r", encoding="utf-8") as f:
        coll_data = json.load(f)
    with env_path.open("r", encoding="utf-8") as f:
        env_data = copy.deepcopy(json.load(f)[0])

    del env_data["variables"]["jira_base_url"]

    with pytest.raises(AssertionError, match="do not match expected manifest collection keys"):
        _assert_environment_structural_consistency(manifest_data, coll_data, env_data)


def test_paired_environments_seeded_defect_extra_key():
    """Seeded defect test: extra variable key not in collection fails structural assertion."""
    manifest_data = _read_manifest_data()
    coll_path = EXAMPLES_ROOT / "collections" / "jira_mcp.json"
    env_path = EXAMPLES_ROOT / "environments" / "jira_cloud.json"

    with coll_path.open("r", encoding="utf-8") as f:
        coll_data = json.load(f)
    with env_path.open("r", encoding="utf-8") as f:
        env_data = copy.deepcopy(json.load(f)[0])

    env_data["variables"]["unexpected_extra_var"] = "foo"

    with pytest.raises(AssertionError, match="do not match expected manifest collection keys"):
        _assert_environment_structural_consistency(manifest_data, coll_data, env_data)


def test_paired_environments_seeded_defect_unhidden_secret():
    """Seeded defect test: secret variable missing from hidden_keys fails structural assertion."""
    manifest_data = _read_manifest_data()
    coll_path = EXAMPLES_ROOT / "collections" / "jira_mcp.json"
    env_path = EXAMPLES_ROOT / "environments" / "jira_cloud.json"

    with coll_path.open("r", encoding="utf-8") as f:
        coll_data = json.load(f)
    with env_path.open("r", encoding="utf-8") as f:
        env_data = copy.deepcopy(json.load(f)[0])

    env_data["hidden_keys"] = []

    with pytest.raises(AssertionError, match="do not match expected secret keys"):
        _assert_environment_structural_consistency(manifest_data, coll_data, env_data)
