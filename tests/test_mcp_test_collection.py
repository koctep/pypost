"""Groundwork tests for the MCP test collection and environment (PYPOST-180)."""
import pytest

import unittest

from pypost.core.mcp_tool_contract import build_mcp_tool_contract_preview
from pypost.core.mcp_tools_overview import collect_mcp_tool_overview
from tests.helpers.mcp_test_collection import (
    EXPECTED_COLLECTION_ID,
    EXPECTED_COLLECTION_NAME,
    EXPECTED_ENV_ID,
    EXPECTED_ENV_NAME,
    EXPECTED_MCP_TOOL_NAMES,
    EXPECTED_REQUEST_COUNT,
    MCP_COLLECTION_PATH,
    MCP_TEST_ENV_PATH,
    load_mcp_test_collection,
    load_mcp_test_environments,
    mcp_test_environment,
)

pytestmark = pytest.mark.timeout(30)


class TestMcpTestCollectionPaths(unittest.TestCase):
    def test_committed_collection_and_environment_files_exist(self):
        self.assertTrue(MCP_COLLECTION_PATH.is_file())
        self.assertTrue(MCP_TEST_ENV_PATH.is_file())


class TestMcpTestCollectionModel(unittest.TestCase):
    def test_collection_parses_with_expected_identity(self):
        collection = load_mcp_test_collection()
        self.assertEqual(collection.id, EXPECTED_COLLECTION_ID)
        self.assertEqual(collection.name, EXPECTED_COLLECTION_NAME)
        self.assertEqual(len(collection.requests), EXPECTED_REQUEST_COUNT)

    def test_exposed_requests_match_mcp_tool_overview(self):
        collection = load_mcp_test_collection()
        tool_names = {
            entry.mcp_name for entry in collect_mcp_tool_overview([collection])
        }
        self.assertEqual(tool_names, EXPECTED_MCP_TOOL_NAMES)

    def test_list_tools_request_is_not_exposed_as_mcp_tool(self):
        collection = load_mcp_test_collection()
        list_tools = next(
            request for request in collection.requests if request.name == "List Tools"
        )
        self.assertFalse(list_tools.expose_as_mcp)
        self.assertEqual(list_tools.method, "MCP")
        self.assertEqual(list_tools.url, "http://127.0.0.1:1080/mcp")

    def test_sse_probe_requests_are_exposed_with_expected_urls(self):
        collection = load_mcp_test_collection()
        by_name = {request.name: request for request in collection.requests}
        metrics = by_name["SSE Probe Metrics"]
        main = by_name["SSE Probe Main"]
        self.assertTrue(metrics.expose_as_mcp)
        self.assertTrue(main.expose_as_mcp)
        self.assertEqual(metrics.url, "http://127.0.0.1:9080/sse")
        self.assertEqual(main.url, "http://127.0.0.1:1080/sse")

    def test_exposed_requests_have_agent_contract_previews(self):
        collection = load_mcp_test_collection()
        exposed = [request for request in collection.requests if request.expose_as_mcp]
        self.assertEqual(len(exposed), len(EXPECTED_MCP_TOOL_NAMES))
        for request in exposed:
            preview = build_mcp_tool_contract_preview(request)
            self.assertIsNotNone(preview)
            self.assertIn(preview.tool_name, EXPECTED_MCP_TOOL_NAMES)


class TestMcpTestEnvironmentModel(unittest.TestCase):
    def test_environment_parses_with_mcp_enabled(self):
        env = mcp_test_environment()
        self.assertEqual(env.id, EXPECTED_ENV_ID)
        self.assertEqual(env.name, EXPECTED_ENV_NAME)
        self.assertTrue(env.enable_mcp)

    def test_environment_file_contains_single_entry(self):
        environments = load_mcp_test_environments()
        self.assertEqual(len(environments), 1)


if __name__ == "__main__":
    unittest.main()
