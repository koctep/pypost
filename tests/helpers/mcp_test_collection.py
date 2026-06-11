"""Shared loaders for the MCP test collection and environment (PYPOST-180)."""

from __future__ import annotations

import json
from pathlib import Path

from pypost.models.models import Collection, Environment, RequestData

REPO_ROOT = Path(__file__).resolve().parents[2]
MCP_COLLECTION_PATH = REPO_ROOT / "examples" / "collections" / "mcp.json"
MCP_TEST_ENV_PATH = REPO_ROOT / "config" / "test" / "environments.json"

EXPECTED_COLLECTION_ID = "test-collection-mcp"
EXPECTED_COLLECTION_NAME = "MCP"
EXPECTED_REQUEST_COUNT = 3
EXPECTED_MCP_TOOL_NAMES = frozenset({"sse_probe_metrics", "sse_probe_main"})
EXPECTED_ENV_ID = "test-env-mcp"
EXPECTED_ENV_NAME = "MCP Test"


def load_mcp_test_collection() -> Collection:
    """Load and validate the committed MCP test collection JSON."""
    data = json.loads(MCP_COLLECTION_PATH.read_text(encoding="utf-8"))
    return Collection.model_validate(data)


def load_mcp_test_environments() -> list[Environment]:
    """Load and validate committed MCP test environment entries."""
    data = json.loads(MCP_TEST_ENV_PATH.read_text(encoding="utf-8"))
    return [Environment.model_validate(item) for item in data]


def mcp_exposed_requests() -> list[RequestData]:
    """Return expose_as_mcp requests from the committed MCP test collection."""
    return [
        request
        for request in load_mcp_test_collection().requests
        if request.expose_as_mcp
    ]


def mcp_test_environment() -> Environment:
    """Return the single MCP Test environment from config/test."""
    environments = load_mcp_test_environments()
    if len(environments) != 1:
        raise ValueError(
            f"expected one MCP test environment, found {len(environments)}"
        )
    return environments[0]
