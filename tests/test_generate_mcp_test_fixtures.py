"""Tests for MCP test fixture generation (PYPOST-179)."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

import pytest

from pypost.fixtures.mcp_test_fixtures import (
    build_mcp_test_collection,
    build_mcp_test_environments,
    fixtures_match_committed,
    serialize_collection,
    serialize_environments,
)
from tests.helpers.mcp_test_collection import (
    EXPECTED_COLLECTION_ID,
    EXPECTED_ENV_ID,
    load_mcp_test_collection,
    mcp_test_environment,
)

pytestmark = pytest.mark.timeout(30)

REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATOR = REPO_ROOT / "scripts" / "generate_mcp_test_fixtures.py"


class TestMcpTestFixtureBuilders(unittest.TestCase):
    def test_builders_match_committed_models(self):
        self.assertTrue(fixtures_match_committed())

    def test_serialized_collection_parses_to_expected_identity(self):
        collection = build_mcp_test_collection()
        parsed = json.loads(serialize_collection(collection))
        self.assertEqual(parsed["id"], EXPECTED_COLLECTION_ID)
        self.assertEqual(len(parsed["requests"]), 3)

    def test_serialized_environments_include_mcp_test_entry(self):
        environments = build_mcp_test_environments()
        parsed = json.loads(serialize_environments(environments))
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["id"], EXPECTED_ENV_ID)
        self.assertTrue(parsed[0]["enable_mcp"])

    def test_committed_files_match_helper_loaders(self):
        self.assertEqual(load_mcp_test_collection(), build_mcp_test_collection())
        self.assertEqual(mcp_test_environment(), build_mcp_test_environments()[0])


class TestGenerateMcpTestFixturesCli(unittest.TestCase):
    def test_check_exits_zero_for_committed_fixtures(self):
        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--check"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)


if __name__ == "__main__":
    unittest.main()
