"""Tests for MCPClientService (MCP method for testing MCP endpoints)."""
import pytest

import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from pypost.core.mcp_client_service import MCPClientService
from pypost.models.errors import ErrorCategory, ExecutionError

pytestmark = pytest.mark.timeout(60)


class MCPClientServiceTests(unittest.TestCase):
    def test_list_tools_returns_json_with_tools(self):
        """list_tools returns ResponseData with JSON body containing tools."""
        service = MCPClientService()
        mock_result = {"tools": [{"name": "echo", "description": "Echo tool"}]}

        with patch.object(
            service, "_run_async", new_callable=AsyncMock, return_value=mock_result
        ):
            result = service.run("http://localhost:1080/mcp", "list_tools", None)

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
                "http://localhost:1080/mcp",
                "call_tool",
                {"name": "foo", "arguments": {"x": 1}},
            )

        self.assertEqual(result.status_code, 200)
        body = json.loads(result.body)
        self.assertIn("content", body)
        self.assertEqual(body["content"][0]["text"], "ok")

    def test_connect_error_raises_execution_error_network(self):
        """httpx.ConnectError raises ExecutionError with NETWORK category."""
        service = MCPClientService()

        with patch.object(
            service,
            "_run_async",
            new_callable=AsyncMock,
            side_effect=httpx.ConnectError("Connection refused"),
        ):
            with self.assertRaises(ExecutionError) as ctx:
                service.run("http://localhost:1080/mcp", "list_tools", None)

        self.assertEqual(ctx.exception.category, ErrorCategory.NETWORK)

    def test_read_timeout_raises_execution_error_timeout(self):
        """httpx.ReadTimeout raises ExecutionError with TIMEOUT category."""
        service = MCPClientService()

        with patch.object(
            service,
            "_run_async",
            new_callable=AsyncMock,
            side_effect=httpx.ReadTimeout("read timed out"),
        ):
            with self.assertRaises(ExecutionError) as ctx:
                service.run("http://localhost:1080/mcp", "list_tools", None)

        self.assertEqual(ctx.exception.category, ErrorCategory.TIMEOUT)

    def test_timeout_raises_execution_error_timeout(self):
        """TimeoutError raises ExecutionError with TIMEOUT category."""
        service = MCPClientService()

        with patch.object(
            service,
            "_run_async",
            new_callable=AsyncMock,
            side_effect=TimeoutError("timed out"),
        ):
            with self.assertRaises(ExecutionError) as ctx:
                service.run("http://localhost:1080/mcp", "list_tools", None)

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
                service.run("http://localhost:1080/mcp", "list_tools", None)

        self.assertEqual(ctx.exception.category, ErrorCategory.UNKNOWN)

    def test_run_passes_headers_to_create_mcp_http_client(self):
        """run() forwards user headers to create_mcp_http_client (not the transport)."""
        service = MCPClientService()
        headers = {"Authorization": "Bearer secret"}
        mock_session = AsyncMock()
        tools_result = MagicMock()
        tools_result.model_dump.return_value = {"tools": [{"name": "echo"}]}
        mock_session.list_tools.return_value = tools_result

        with (
            patch(
                "pypost.core.mcp_client_service.create_mcp_http_client"
            ) as mock_create,
            patch(
                "pypost.core.mcp_client_service.streamable_http_client"
            ) as mock_streamable,
            patch(
                "pypost.core.mcp_client_service.ClientSession"
            ) as mock_session_cls,
        ):
            mock_create.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
            mock_create.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_streamable.return_value.__aenter__ = AsyncMock(
                return_value=(MagicMock(), MagicMock(), MagicMock())
            )
            mock_streamable.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_session_cls.return_value.__aenter__ = AsyncMock(
                return_value=mock_session
            )
            mock_session_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            result = service.run(
                "http://localhost:1080/mcp",
                "list_tools",
                None,
                headers=headers,
            )

        self.assertEqual(200, result.status_code)
        mock_create.assert_called_once()
        self.assertEqual(headers, mock_create.call_args.kwargs["headers"])
        self.assertIn("timeout", mock_create.call_args.kwargs)

    def test_run_logs_header_count_not_values(self):
        """mcp_operation_start logs header_count; never logs header values."""
        service = MCPClientService()
        secret = "Bearer super-secret-token"
        with patch.object(
            service, "_run_async", new_callable=AsyncMock, return_value={"tools": []}
        ):
            with self.assertLogs(
                "pypost.core.mcp_client_service", level="DEBUG"
            ) as captured:
                service.run(
                    "http://localhost:1080/mcp",
                    "list_tools",
                    None,
                    headers={"Authorization": secret},
                )
        joined = "\n".join(captured.output)
        self.assertIn("mcp_operation_start", joined)
        self.assertIn("header_count=1", joined)
        self.assertNotIn(secret, joined)
        self.assertNotIn("Bearer", joined)

    def test_run_logs_zero_header_count_when_headers_omitted(self):
        """mcp_operation_start reports header_count=0 when headers are omitted."""
        service = MCPClientService()
        with patch.object(
            service, "_run_async", new_callable=AsyncMock, return_value={"tools": []}
        ):
            with self.assertLogs(
                "pypost.core.mcp_client_service", level="DEBUG"
            ) as captured:
                service.run("http://localhost:1080/mcp", "list_tools", None)
        joined = "\n".join(captured.output)
        self.assertIn("header_count=0", joined)
