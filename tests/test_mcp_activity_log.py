"""Tests for MCP activity log (PYPOST-141)."""
import pytest

pytestmark = pytest.mark.timeout(30)

import asyncio
import unittest
from unittest.mock import MagicMock

from pypost.core.mcp_activity_log import McpActivityEntry, McpActivityLog
from pypost.core.mcp_server_impl import MCPServerImpl
from pypost.core.request_service import ExecutionResult
from pypost.models.models import RequestData
from pypost.models.response import ResponseData


def _exec_result(body="ok", status_code=200):
    return ExecutionResult(
        response=ResponseData(
            status_code=status_code,
            headers={},
            body=body,
            elapsed_time=0.01,
            size=len(body.encode("utf-8")),
        ),
        updated_variables={},
        script_logs=[],
        execution_error=None,
    )


class TestMcpActivityLog(unittest.TestCase):
    def test_append_and_get_entries_newest_first(self):
        log = McpActivityLog(max_entries=10)
        first = McpActivityEntry.new_list_tools(1)
        second = McpActivityEntry.new_call_tool(
            "echo",
            outcome="success",
            mcp_arg_count=0,
            http_status=200,
        )
        log.append(first)
        log.append(second)
        entries = log.get_entries()
        self.assertEqual(len(entries), 2)
        self.assertIs(entries[0], second)
        self.assertIs(entries[1], first)

    def test_ring_buffer_drops_oldest(self):
        log = McpActivityLog(max_entries=2)
        for count in range(3):
            log.append(McpActivityEntry.new_list_tools(count))
        self.assertEqual(log.count(), 2)
        entries = log.get_entries()
        self.assertEqual(entries[0].tool_count, 2)
        self.assertEqual(entries[1].tool_count, 1)

    def test_on_append_callback(self):
        seen: list[McpActivityEntry] = []
        log = McpActivityLog(on_append=seen.append)
        entry = McpActivityEntry.new_list_tools(4)
        log.append(entry)
        self.assertEqual(seen, [entry])

    def test_clear(self):
        log = McpActivityLog()
        log.append(McpActivityEntry.new_list_tools(1))
        log.clear()
        self.assertEqual(log.count(), 0)
        self.assertEqual(log.get_entries(), [])


class TestMcpServerImplActivity(unittest.TestCase):
    def test_list_tools_records_activity(self):
        log = McpActivityLog()
        impl = MCPServerImpl(activity_log=log)
        req = RequestData(
            name="Echo",
            expose_as_mcp=True,
            method="GET",
            url="http://example.com",
        )
        impl.register_tools([req])
        asyncio.run(impl.list_tools())
        entries = log.get_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].operation, "list_tools")
        self.assertEqual(entries[0].tool_count, 1)
        self.assertEqual(entries[0].outcome, "success")

    def test_call_tool_records_success(self):
        log = McpActivityLog()
        impl = MCPServerImpl(activity_log=log)
        req = RequestData(
            name="Echo",
            expose_as_mcp=True,
            method="GET",
            url="http://example.com",
        )
        impl.register_tools([req])
        impl.request_service.execute = MagicMock(return_value=_exec_result("ok"))
        asyncio.run(impl.call_tool("echo", {"host": "x"}))
        entries = log.get_entries()
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry.operation, "call_tool")
        self.assertEqual(entry.tool_name, "echo")
        self.assertEqual(entry.outcome, "success")
        self.assertEqual(entry.mcp_arg_count, 1)
        self.assertEqual(entry.http_status, 200)
        self.assertIsNotNone(entry.duration_ms)


if __name__ == "__main__":
    unittest.main()
