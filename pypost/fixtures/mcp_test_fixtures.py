"""Builders for the MCP manual-test collection and environment (PYPOST-179)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from pypost.models.models import Collection, Environment, RequestData

REPO_ROOT = Path(__file__).resolve().parents[2]
MCP_COLLECTION_PATH = REPO_ROOT / "examples" / "collections" / "mcp.json"
MCP_TEST_ENV_PATH = REPO_ROOT / "config" / "test" / "environments.json"


def build_mcp_test_collection() -> Collection:
    """Return the MCP test collection used for manual and CI validation."""
    return Collection(
        id="test-collection-mcp",
        name="MCP",
        requests=[
            RequestData(
                id="sse-probe-metrics",
                name="SSE Probe Metrics",
                method="GET",
                url="http://127.0.0.1:9080/sse",
                expose_as_mcp=True,
            ),
            RequestData(
                id="sse-probe-main",
                name="SSE Probe Main",
                method="GET",
                url="http://127.0.0.1:1080/sse",
                expose_as_mcp=True,
            ),
            RequestData(
                id="mcp-list-tools",
                name="List Tools",
                method="MCP",
                url="http://127.0.0.1:1080/mcp",
                expose_as_mcp=False,
            ),
        ],
    )


def build_mcp_test_environments() -> list[Environment]:
    """Return the MCP Test environment entries for config/test."""
    return [
        Environment(
            id="test-env-mcp",
            name="MCP Test",
            enable_mcp=True,
        ),
    ]


def serialize_collection(collection: Collection) -> str:
    """Serialize a collection the same way StorageManager persists collections."""
    return collection.model_dump_json(indent=2) + "\n"


def serialize_environments(environments: Iterable[Environment]) -> str:
    """Serialize environments for config/test/environments.json."""
    payload = [environment.model_dump(mode="json") for environment in environments]
    return json.dumps(payload, indent=2) + "\n"


def fixtures_match_committed() -> bool:
    """Return True when generated fixtures match committed files (model equality)."""
    if not MCP_COLLECTION_PATH.is_file() or not MCP_TEST_ENV_PATH.is_file():
        return False
    committed_collection = Collection.model_validate_json(
        MCP_COLLECTION_PATH.read_text(encoding="utf-8"),
    )
    committed_envs = [
        Environment.model_validate(item)
        for item in json.loads(MCP_TEST_ENV_PATH.read_text(encoding="utf-8"))
    ]
    return (
        build_mcp_test_collection() == committed_collection
        and build_mcp_test_environments() == committed_envs
    )
