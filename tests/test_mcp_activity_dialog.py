"""GUI tests for McpActivityDialog (PYPOST-721)."""
import pytest

pytestmark = pytest.mark.timeout(60)

from pypost.core.mcp_activity_log import McpActivityEntry
from pypost.ui.dialogs.mcp_activity_dialog import (
    McpActivityDialog,
    _format_details,
    _format_timestamp,
    _format_tool_column,
)


def _list_tools_entry(tool_count: int = 3) -> McpActivityEntry:
    return McpActivityEntry.new_list_tools(tool_count=tool_count)


def _call_tool_entry(**kwargs) -> McpActivityEntry:
    return McpActivityEntry.new_call_tool(
        "get_user",
        outcome="success",
        mcp_arg_count=kwargs.get("mcp_arg_count", 2),
        http_status=kwargs.get("http_status", 200),
        detail=kwargs.get("detail"),
        duration_ms=kwargs.get("duration_ms", 42.5),
    )


class TestMcpActivityDialog:
    def test_empty_entries_shows_no_mcp_activity_text(self, qapp):
        dlg = McpActivityDialog([])
        try:
            assert "No MCP activity" in dlg._summary_label.text()
            assert dlg._table.isHidden()
        finally:
            dlg.close()

    def test_entries_shows_count_in_summary(self, qapp):
        entries = [_list_tools_entry(), _call_tool_entry()]
        dlg = McpActivityDialog(entries)
        try:
            assert "2" in dlg._summary_label.text()
            assert not dlg._table.isHidden()
        finally:
            dlg.close()

    def test_table_row_count_matches_entries(self, qapp):
        entries = [_list_tools_entry(), _call_tool_entry()]
        dlg = McpActivityDialog(entries)
        try:
            assert dlg._table.rowCount() == 2
        finally:
            dlg.close()

    def test_set_entries_replaces_content(self, qapp):
        dlg = McpActivityDialog([])
        try:
            assert dlg._table.rowCount() == 0
            dlg.set_entries([_list_tools_entry()])
            assert dlg._table.rowCount() == 1
            assert not dlg._table.isHidden()
        finally:
            dlg.close()

    def test_set_entries_to_empty_hides_table(self, qapp):
        dlg = McpActivityDialog([_list_tools_entry()])
        try:
            dlg.set_entries([])
            assert dlg._table.isHidden()
        finally:
            dlg.close()


class TestMcpActivityDialogFormatters:
    def test_format_timestamp_returns_time_string(self):
        entry = _list_tools_entry()
        result = _format_timestamp(entry)
        assert ":" in result  # HH:MM:SS

    def test_format_tool_column_list_tools(self):
        entry = _list_tools_entry(3)
        assert _format_tool_column(entry) == "3 tool(s)"

    def test_format_tool_column_list_tools_none_count(self):
        entry = McpActivityEntry(
            id="x",
            timestamp=_list_tools_entry().timestamp,
            operation="list_tools",
            outcome="success",
            tool_count=None,
        )
        assert _format_tool_column(entry) == "0 tool(s)"

    def test_format_tool_column_call_tool(self):
        entry = _call_tool_entry()
        assert _format_tool_column(entry) == "get_user"

    def test_format_details_includes_all_fields(self):
        entry = _call_tool_entry(mcp_arg_count=2, http_status=201, duration_ms=99.9, detail="ok")
        result = _format_details(entry)
        assert "args=2" in result
        assert "status=201" in result
        assert "100ms" in result
        assert "ok" in result

    def test_format_details_empty_when_no_optional_fields(self):
        entry = McpActivityEntry(
            id="x",
            timestamp=_list_tools_entry().timestamp,
            operation="call_tool",
            outcome="success",
        )
        assert _format_details(entry) == ""
