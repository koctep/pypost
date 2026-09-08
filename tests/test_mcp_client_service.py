"""Tests for MCPClientService (MCP method for testing MCP endpoints)."""
import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from pypost.core.mcp_client_service import MCPClientService
from pypost.models.errors import ErrorCategory, ExecutionError


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

    def test_connection_error_raises_execution_error_network(self):
        """Connection error raises ExecutionError with NETWORK category."""
        service = MCPClientService()

        with patch.object(
            service,
            "_run_async",
            new_callable=AsyncMock,
            side_effect=ConnectionError("Connection refused"),
        ):
            with self.assertRaises(ExecutionError) as ctx:
                service.run("http://localhost:1080/sse", "list_tools", None)

        self.assertEqual(ctx.exception.category, ErrorCategory.NETWORK)

    def test_timeout_raises_execution_error_timeout(self):
        """asyncio.TimeoutError raises ExecutionError with TIMEOUT category."""
        import asyncio
        service = MCPClientService()

        with patch.object(
            service,
            "_run_async",
            new_callable=AsyncMock,
            side_effect=asyncio.TimeoutError(),
        ):
            with self.assertRaises(ExecutionError) as ctx:
                service.run("http://localhost:1080/sse", "list_tools", None)

        self.assertEqual(ctx.exception.category, ErrorCategory.TIMEOUT)

    def test_unknown_error_raises_execution_error_unknown(self):
        """Generic exception raises ExecutionError with UNKNOWN category."""
        service = MCPClientService()

        with patch.object(
            service,
            "_run_async",
            new_callable=AsyncMock,
            side_effect=RuntimeError("something broke"),
        ):
            with self.assertRaises(ExecutionError) as ctx:
                service.run("http://localhost:1080/sse", "list_tools", None)

        self.assertEqual(ctx.exception.category, ErrorCategory.UNKNOWN)


class MCPClientSessionLifecycleTests(unittest.TestCase):
    """The session must be entered as a context manager, not merely constructed.

    ClientSession.__aenter__ starts the receive loop; without it initialize()
    waits for a reply nothing is reading and the call dies on the total timeout.
    """

    @staticmethod
    def _patched_transport():
        streams = AsyncMock()
        streams.__aenter__.return_value = (MagicMock(), MagicMock())
        return patch(
            "pypost.core.mcp_client_service.sse_client", return_value=streams
        )

    def test_list_tools_enters_the_session(self):
        service = MCPClientService()
        session = AsyncMock()
        session.__aenter__.return_value = session
        session.list_tools.return_value = MagicMock(
            model_dump=MagicMock(return_value={"tools": []})
        )

        with self._patched_transport(), patch(
            "pypost.core.mcp_client_service.ClientSession", return_value=session
        ):
            result = service.run("http://localhost:1080/sse", "list_tools", None)

        session.__aenter__.assert_awaited_once()
        session.initialize.assert_awaited_once()
        self.assertEqual(200, result.status_code)

    def test_call_tool_enters_the_session(self):
        service = MCPClientService()
        session = AsyncMock()
        session.__aenter__.return_value = session
        session.call_tool.return_value = MagicMock(
            model_dump=MagicMock(return_value={"content": []})
        )

        with self._patched_transport(), patch(
            "pypost.core.mcp_client_service.ClientSession", return_value=session
        ):
            service.run(
                "http://localhost:1080/sse",
                "call_tool",
                {"name": "echo", "arguments": {"x": 1}},
            )

        session.__aenter__.assert_awaited_once()
        session.call_tool.assert_awaited_once_with("echo", {"x": 1})

