"""GUI tests for McpToolsOverviewDialog (PYPOST-721)."""
import pytest

from pypost.core.mcp_tools_overview import McpToolOverviewEntry
from pypost.ui.dialogs.mcp_tools_overview_dialog import McpToolsOverviewDialog

pytestmark = pytest.mark.timeout(60)


def _entry(**kwargs) -> McpToolOverviewEntry:
    return McpToolOverviewEntry(
        mcp_name=kwargs.get("mcp_name", "get_user"),
        request_name=kwargs.get("request_name", "Get User"),
        collection_name=kwargs.get("collection_name", "API"),
        method=kwargs.get("method", "GET"),
        description=kwargs.get("description", "Fetch a user"),
    )


class TestMcpToolsOverviewDialog:
    def test_empty_entries_shows_no_tools_message(self, qapp):
        dlg = McpToolsOverviewDialog([])
        try:
            labels = dlg.findChildren(__import__("PySide6.QtWidgets", fromlist=["QLabel"]).QLabel)
            texts = [lbl.text() for lbl in labels]
            assert any("No requests" in t for t in texts)
        finally:
            dlg.close()

    def test_entries_show_count_in_summary(self, qapp):
        entries = [_entry(), _entry(mcp_name="list_items", request_name="List Items")]
        dlg = McpToolsOverviewDialog(entries)
        try:
            from PySide6.QtWidgets import QLabel
            labels = dlg.findChildren(QLabel)
            texts = [lbl.text() for lbl in labels]
            assert any("2" in t for t in texts)
        finally:
            dlg.close()

    def test_table_row_count_matches_entries(self, qapp):
        entries = [_entry(), _entry(mcp_name="b", request_name="B")]
        dlg = McpToolsOverviewDialog(entries)
        try:
            from PySide6.QtWidgets import QTableWidget
            tables = dlg.findChildren(QTableWidget)
            assert tables
            assert tables[0].rowCount() == 2
        finally:
            dlg.close()

    def test_table_is_hidden_for_empty_entries(self, qapp):
        dlg = McpToolsOverviewDialog([])
        try:
            from PySide6.QtWidgets import QTableWidget
            tables = dlg.findChildren(QTableWidget)
            assert tables
            assert tables[0].isHidden()
        finally:
            dlg.close()

    def test_table_row_content(self, qapp):
        entry = _entry(mcp_name="get_user", request_name="Get User", collection_name="API",
                       method="GET", description="desc")
        dlg = McpToolsOverviewDialog([entry])
        try:
            from PySide6.QtWidgets import QTableWidget
            tables = dlg.findChildren(QTableWidget)
            t = tables[0]
            assert t.item(0, 0).text() == "get_user"
            assert t.item(0, 1).text() == "Get User"
            assert t.item(0, 2).text() == "API"
            assert t.item(0, 3).text() == "GET"
            assert t.item(0, 4).text() == "desc"
        finally:
            dlg.close()
