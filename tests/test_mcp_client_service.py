"""Tests for MCPClientService (MCP method for testing MCP endpoints)."""
import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from pypost.core.mcp_client_service import MCPClientService


class MCPClientServiceTests(unittest.TestCase):
    def test_list_tools_returns_json_with_tools(self):
        """list_tools returns ResponseData with JSON body containing tools."""
        service = MCPClientService()
        mock_result = {"tools": [{"name": "echo", "description": "Echo tool"}]}

        with patch.object(
            service, "_run_async", new_callable=AsyncMock, return_value=mock_result
        ):
            result = service.run("http://localhost:1080/sse", "list_tools", None)

        self.assertEqual(result.status_code, 200)
        self.assertIn("Content-Type", result.headers)
        self.assertEqual(result.headers["Content-Type"], "application/json")
        body = json.loads(result.body)
        self.assertIn("tools", body)
        self.assertEqual(len(body["tools"]), 1)
        self.assertEqual(body["tools"][0]["name"], "echo")

    def test_call_tool_returns_result(self):
        """call_tool with name and arguments returns result."""
        service = MCPClientService()
        mock_result = {"content": [{"type": "text", "text": "ok"}]}

        with patch.object(
            service, "_run_async", new_callable=AsyncMock, return_value=mock_result
        ):
            result = service.run(
                "http://localhost:1080/sse",
                "call_tool",
                {"name": "foo", "arguments": {"x": 1}},
            )

        self.assertEqual(result.status_code, 200)
        body = json.loads(result.body)
        self.assertIn("content", body)
        self.assertEqual(body["content"][0]["text"], "ok")

    def test_connection_error_returns_500_with_error_message(self):
        """Connection error returns status 500 and error in body."""
        service = MCPClientService()

        with patch.object(
            service,
            "_run_async",
            new_callable=AsyncMock,
            side_effect=ConnectionError("Connection refused"),
        ):
            result = service.run("http://localhost:1080/sse", "list_tools", None)

        self.assertEqual(result.status_code, 500)
        body = json.loads(result.body)
        self.assertIn("error", body)
        self.assertIn("Connection refused", body["error"])
