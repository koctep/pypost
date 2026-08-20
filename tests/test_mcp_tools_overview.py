"""Tests for MCP tools overview collection (PYPOST-556)."""
import pytest

import unittest

from pypost.core.mcp_tools_overview import collect_mcp_tool_overview
from pypost.models.models import Collection, RequestData

pytestmark = pytest.mark.timeout(30)


class TestMcpToolsOverview(unittest.TestCase):
    def test_collects_exposed_requests_only(self):
        exposed = RequestData(
            id="r1",
            name="Get User",
            expose_as_mcp=True,
            mcp_description="Fetch a user",
            method="GET",
        )
        hidden = RequestData(id="r2", name="Secret", expose_as_mcp=False)
        col = Collection(id="c1", name="API", requests=[exposed, hidden])
        entries = collect_mcp_tool_overview([col])
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].mcp_name, "get_user")
        self.assertEqual(entries[0].collection_name, "API")
        self.assertEqual(entries[0].description, "Fetch a user")

    def test_sorted_by_mcp_name(self):
        a = RequestData(id="r1", name="Zebra", expose_as_mcp=True)
        b = RequestData(id="r2", name="Alpha", expose_as_mcp=True)
        col = Collection(id="c1", name="C", requests=[a, b])
        names = [entry.mcp_name for entry in collect_mcp_tool_overview([col])]
        self.assertEqual(names, ["alpha", "zebra"])


if __name__ == "__main__":
    unittest.main()
