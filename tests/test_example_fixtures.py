"""Contract tests for shipped examples/ fixtures (PYPOST-1017)."""

from __future__ import annotations

from pathlib import Path

import pytest

from pypost.core.collection_import import load_collection_import_candidates
from pypost.core.environment_import import load_import_candidates
from pypost.core.storage import StorageManager

pytestmark = pytest.mark.timeout(30)

REPO_ROOT = Path(__file__).resolve().parents[1]
JIRA_COLLECTION_PATH = REPO_ROOT / "examples" / "collections" / "jira_mcp.json"
JIRA_ENV_PATH = REPO_ROOT / "examples" / "environments" / "jira_cloud.json"
MCP_PROBE_PATH = REPO_ROOT / "examples" / "collections" / "mcp.json"

PLACEHOLDER_BASE_URL = "https://your-team.atlassian.net"
PLACEHOLDER_CREDENTIALS = "you@example.com:your-api-token"


def _make_storage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> StorageManager:
    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_ENABLED", raising=False)
    monkeypatch.delenv("PYPOST_ENV_ENCRYPTION_KEY", raising=False)
    return StorageManager(data_dir=tmp_path / "pypost-data")


def test_jira_mcp_collection_imports_via_native_loader():
    collections, parse_errors = load_collection_import_candidates(JIRA_COLLECTION_PATH)

    assert parse_errors == []
    assert len(collections) == 1
    collection = collections[0]
    assert collection.id == "jira-cloud-mcp"
    assert collection.name == "Jira Cloud MCP"
    assert len(collection.requests) == 12
    assert all(request.expose_as_mcp for request in collection.requests)

    text = JIRA_COLLECTION_PATH.read_text(encoding="utf-8")
    assert "{{ jira_base_url }}" in text
    assert "base64(jira_credentials)" in text
    assert PLACEHOLDER_CREDENTIALS not in text


def test_jira_cloud_environment_imports_with_placeholders(tmp_path, monkeypatch):
    storage = _make_storage(tmp_path, monkeypatch)
    environments, parse_errors = load_import_candidates(JIRA_ENV_PATH, storage)

    assert parse_errors == []
    assert len(environments) == 1
    environment = environments[0]
    assert environment.id == "jira-cloud-mcp-environment"
    assert environment.name == "Jira Cloud MCP"
    assert environment.variables["jira_base_url"] == PLACEHOLDER_BASE_URL
    assert environment.variables["jira_credentials"] == PLACEHOLDER_CREDENTIALS
    assert "jira_credentials" in environment.hidden_keys
    assert environment.enable_mcp is True


def test_mcp_probe_collection_still_imports():
    collections, parse_errors = load_collection_import_candidates(MCP_PROBE_PATH)

    assert parse_errors == []
    assert len(collections) == 1
    assert collections[0].id == "test-collection-mcp"
    assert collections[0].name == "MCP"
    assert len(collections[0].requests) == 3
