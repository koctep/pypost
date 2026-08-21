"""Tests for MCP Proxy Server: configuration, dynamic header resolution,
protocol forwarding, secrets masking, and upstream error handling.
"""
from __future__ import annotations

import asyncio
import logging
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from pydantic import ValidationError

from pypost.core.mcp_activity_log import McpActivityLog
from pypost.core.mcp_proxy_headers import (
    McpUnresolvedVariableError,
    resolve_proxy_headers,
    sanitize_proxy_headers,
)
from pypost.core.mcp_proxy_server_impl import MCPProxyServerImpl
from pypost.core.mcp_server_registry import MCPServerRegistry
from pypost.core.mcp_transport_routes import (
    MCP_LEGACY_SSE_MOUNT_PATH,
    MCP_STREAMABLE_HTTP_PATH,
)
from pypost.core.qt.mcp_server import MCPServerManager
from pypost.models.settings import McpServerConfiguration

pytestmark = pytest.mark.timeout(60)


class TestMcpServerConfigurationProxy(unittest.TestCase):
    """Tests for McpServerConfiguration proxy attributes and validation."""

    def test_proxy_configuration_valid(self):
        """Proxy configuration with upstream_url, transport, and headers is valid."""
        config = McpServerConfiguration(
            id="proxy-1",
            name="Remote Jira MCP",
            host="127.0.0.1",
            port=2080,
            server_type="proxy",
            upstream_url="http://localhost:8080/mcp",
            upstream_transport="streamable_http",
            headers={"Authorization": "Bearer {{ JIRA_TOKEN }}"},
            environment_id="env-1",
            enabled=True,
        )
        self.assertEqual(config.server_type, "proxy")
        self.assertEqual(config.upstream_url, "http://localhost:8080/mcp")
        self.assertEqual(config.upstream_transport, "streamable_http")
        self.assertEqual(config.headers, {"Authorization": "Bearer {{ JIRA_TOKEN }}"})
        self.assertIsNone(config.collection_id)

    def test_proxy_configuration_requires_upstream_url(self):
        """Proxy server type requires non-empty upstream_url."""
        with self.assertRaises(ValidationError):
            McpServerConfiguration(
                id="proxy-err",
                port=2081,
                server_type="proxy",
                upstream_url=None,
                environment_id="env-1",
            )

    def test_local_configuration_requires_collection_id(self):
        """Local server type requires collection_id."""
        with self.assertRaises(ValidationError):
            McpServerConfiguration(
                id="local-err",
                port=2082,
                server_type="local",
                collection_id=None,
                environment_id="env-1",
            )


class TestMcpProxyHeaderResolution(unittest.TestCase):
    """Tests for dynamic template resolution and secrets sanitization in proxy headers."""

    def test_resolve_proxy_headers_with_environment_variables(self):
        """Variables in {{ VAR }} syntax are resolved against active environment."""
        headers = {
            "Authorization": "Bearer {{ API_TOKEN }}",
            "X-Tenant-Id": "{{ TENANT_ID }}",
            "Static-Header": "constant-value",
        }
        env_vars = {
            "API_TOKEN": "secret-token-123",
            "TENANT_ID": "tenant-456",
        }
        resolved = resolve_proxy_headers(headers, env_vars)
        self.assertEqual(
            resolved,
            {
                "Authorization": "Bearer secret-token-123",
                "X-Tenant-Id": "tenant-456",
                "Static-Header": "constant-value",
            },
        )

    def test_resolve_proxy_headers_raises_for_missing_variable(self):
        """Referencing an undefined variable raises McpUnresolvedVariableError."""
        headers = {"Authorization": "Bearer {{ MISSING_KEY }}"}
        env_vars = {"OTHER_KEY": "val"}

        with self.assertRaises(McpUnresolvedVariableError) as ctx:
            resolve_proxy_headers(headers, env_vars)
        self.assertIn("MISSING_KEY", str(ctx.exception))

    def test_sanitize_proxy_headers_masks_sensitive_keys_and_hidden_secrets(self):
        """Sensitive header names and values matching hidden_keys are masked."""
        headers = {
            "Authorization": "Bearer secret-token-123",
            "X-API-Key": "my-secret-key",
            "X-Custom-Env": "sensitive-value",
            "X-Public": "public-value",
        }
        env_vars = {
            "API_TOKEN": "secret-token-123",
            "SECRET_VAR": "sensitive-value",
        }
        hidden_keys = {"API_TOKEN", "SECRET_VAR"}

        sanitized = sanitize_proxy_headers(
            headers, env_vars=env_vars, hidden_keys=hidden_keys
        )
        self.assertEqual(sanitized["Authorization"], "Bearer ***")
        self.assertEqual(sanitized["X-API-Key"], "***")
        self.assertEqual(sanitized["X-Custom-Env"], "***")
        self.assertEqual(sanitized["X-Public"], "public-value")


class TestMcpProxyServerImpl(unittest.TestCase):
    """Tests for MCPProxyServerImpl protocol forwarding, lifecycle, and diagnostics."""

    def setUp(self):
        self.activity_log = McpActivityLog()
        self.env_vars = {"JIRA_TOKEN": "secret-jira-token"}
        self.hidden_keys = {"JIRA_TOKEN"}
        self.proxy_impl = MCPProxyServerImpl(
            name="ProxyTestServer",
            upstream_url="http://localhost:9090/mcp",
            upstream_transport="streamable_http",
            headers={"Authorization": "Bearer {{ JIRA_TOKEN }}"},
            variable_supplier=lambda: self.env_vars,
            hidden_keys_supplier=lambda: self.hidden_keys,
            activity_log=self.activity_log,
        )

    def test_proxy_creates_starlette_app_with_mcp_and_sse_routes(self):
        """Proxy exposes Starlette application hosting Streamable HTTP and SSE routes."""
        app = self.proxy_impl.create_app()
        routes = [getattr(r, "path", getattr(r, "path_format", str(r))) for r in app.routes]
        self.assertIn(MCP_STREAMABLE_HTTP_PATH, routes)
        self.assertTrue(any(MCP_LEGACY_SSE_MOUNT_PATH in r for r in routes))

    def test_proxy_forwards_list_tools_to_upstream(self):
        """list_tools queries upstream MCP server and returns its tools."""
        mock_tool = MagicMock(name="upstream_tool", description="Upstream Tool")
        mock_tool.name = "jira_get_issue"
        mock_tool.description = "Fetch issue from Jira"
        mock_tool.inputSchema = {"type": "object", "properties": {"issue_key": {"type": "string"}}}

        mock_session = AsyncMock()
        mock_session.list_tools.return_value = MagicMock(tools=[mock_tool])

        with patch.object(self.proxy_impl, "_connect_upstream") as mock_connect:
            mock_connect.return_value.__aenter__.return_value = mock_session

            tools = asyncio.run(self.proxy_impl.list_tools())
            self.assertEqual(len(tools), 1)
            self.assertEqual(tools[0].name, "jira_get_issue")
            self.assertEqual(tools[0].description, "Fetch issue from Jira")

    def test_proxy_forwards_call_tool_to_upstream(self):
        """call_tool dispatches tool call to upstream MCP server."""
        mock_result = MagicMock()
        mock_result.content = [MagicMock(text='{"issue": "PYPOST-1092"}')]
        mock_result.isError = False

        mock_session = AsyncMock()
        mock_session.call_tool.return_value = mock_result

        with patch.object(self.proxy_impl, "_connect_upstream") as mock_connect:
            mock_connect.return_value.__aenter__.return_value = mock_session

            result = asyncio.run(
                self.proxy_impl.call_tool("jira_get_issue", {"issue_key": "PYPOST-1092"})
            )
            mock_session.call_tool.assert_awaited_once_with(
                "jira_get_issue", {"issue_key": "PYPOST-1092"}
            )
            self.assertEqual(result, mock_result)

    def test_proxy_forwards_prompts_and_resources(self):
        """Proxy server forwards prompt and resource protocol methods to upstream."""
        mock_session = AsyncMock()
        mock_session.list_prompts.return_value = MagicMock(prompts=[MagicMock(name="p1")])
        mock_session.get_prompt.return_value = MagicMock(description="prompt desc")
        mock_session.list_resources.return_value = MagicMock(resources=[MagicMock(uri="res://1")])
        mock_session.read_resource.return_value = MagicMock(contents=[MagicMock(text="data")])

        with patch.object(self.proxy_impl, "_connect_upstream") as mock_connect:
            mock_connect.return_value.__aenter__.return_value = mock_session

            prompts = asyncio.run(self.proxy_impl.list_prompts())
            self.assertEqual(len(prompts), 1)

            prompt = asyncio.run(self.proxy_impl.get_prompt("p1", {}))
            self.assertEqual(prompt.description, "prompt desc")

            resources = asyncio.run(self.proxy_impl.list_resources())
            self.assertEqual(len(resources), 1)

            data = asyncio.run(self.proxy_impl.read_resource("res://1"))
            self.assertEqual(data.contents[0].text, "data")

    def test_proxy_dynamic_headers_passed_to_connect_upstream(self):
        """_connect_upstream receives dynamic headers resolved from current environment."""
        with patch.object(self.proxy_impl, "_connect_upstream") as mock_connect:
            mock_session = AsyncMock()
            mock_session.list_tools.return_value = MagicMock(tools=[])
            mock_connect.return_value.__aenter__.return_value = mock_session

            asyncio.run(self.proxy_impl.list_tools())
            mock_connect.assert_called_once()
            call_args = mock_connect.call_args
            passed_headers = (
                call_args[0][0] if call_args[0] else call_args[1]["headers"]
            )
            self.assertEqual(passed_headers.get("Authorization"), "Bearer secret-jira-token")

    def test_proxy_missing_env_var_aborts_without_upstream_connection(self):
        """Missing required environment variable aborts dispatch and does not connect."""
        self.env_vars.clear()  # JIRA_TOKEN is missing

        with patch.object(self.proxy_impl, "_connect_upstream") as mock_connect:
            with self.assertRaises(Exception):
                asyncio.run(self.proxy_impl.list_tools())
            mock_connect.assert_not_called()

    def test_proxy_logs_activity_with_masked_headers(self):
        """Proxy execution records entry in McpActivityLog with masked header values."""
        mock_session = AsyncMock()
        mock_session.call_tool.return_value = MagicMock(content=[], isError=False)

        with patch.object(self.proxy_impl, "_connect_upstream") as mock_connect:
            mock_connect.return_value.__aenter__.return_value = mock_session

            asyncio.run(self.proxy_impl.call_tool("jira_get_issue", {"key": "PYPOST-1"}))

            entries = self.activity_log.get_entries()
            self.assertGreater(len(entries), 0)
            last_entry = entries[-1]
            self.assertIn("jira_get_issue", last_entry.tool_name or last_entry.operation)
            # Verify plaintext token is never logged
            self.assertNotIn("secret-jira-token", str(last_entry.details))

    def test_proxy_handles_upstream_connection_error(self):
        """Upstream network connection error is mapped to structured MCP error."""
        with patch.object(
            self.proxy_impl,
            "_connect_upstream",
            side_effect=httpx.ConnectError("Connection refused"),
        ):
            with self.assertRaises(Exception) as ctx:
                asyncio.run(self.proxy_impl.list_tools())
            self.assertIn("Connection", str(ctx.exception))

    def test_proxy_handles_upstream_timeout(self):
        """Upstream timeout error is mapped to structured MCP timeout error."""
        with patch.object(
            self.proxy_impl,
            "_connect_upstream",
            side_effect=httpx.ReadTimeout("Request timed out"),
        ):
            with self.assertRaises(Exception) as ctx:
                asyncio.run(self.proxy_impl.list_tools())
            self.assertIn("timed out", str(ctx.exception).lower())

    def test_proxy_tracks_metrics_on_call_tool_success(self):
        """call_tool records metrics for request received, response sent, and duration."""
        mock_metrics = MagicMock()
        self.proxy_impl._metrics = mock_metrics

        mock_session = AsyncMock()
        mock_session.call_tool.return_value = MagicMock(content=[], isError=False)

        with patch.object(self.proxy_impl, "_connect_upstream") as mock_connect:
            mock_connect.return_value.__aenter__.return_value = mock_session

            asyncio.run(self.proxy_impl.call_tool("jira_get_issue", {"key": "PYPOST-1"}))

            mock_metrics.track_mcp_request_received.assert_called_once_with("POST")
            mock_metrics.track_mcp_response_sent.assert_called_once_with("POST", "success")
            mock_metrics.track_mcp_tool_call_duration.assert_called_once()

    def test_proxy_tracks_metrics_on_call_tool_error(self):
        """call_tool records error metrics when upstream connection fails."""
        mock_metrics = MagicMock()
        self.proxy_impl._metrics = mock_metrics

        with patch.object(
            self.proxy_impl,
            "_connect_upstream",
            side_effect=httpx.ConnectError("Connection refused"),
        ):
            with self.assertRaises(Exception):
                asyncio.run(self.proxy_impl.call_tool("jira_get_issue", {"key": "PYPOST-1"}))

            mock_metrics.track_mcp_request_received.assert_called_once_with("POST")
            mock_metrics.track_mcp_response_sent.assert_called_once_with("POST", "error")
            mock_metrics.track_mcp_tool_call_duration.assert_called_once()


@pytest.mark.parametrize("operation", ["list_tools", "call_tool"])
@pytest.mark.parametrize(
    "failure",
    [httpx.ReadTimeout, httpx.ConnectError, RuntimeError],
    ids=["timeout", "connect", "generic"],
)
def test_proxy_failure_logs_and_activity_never_expose_raw_error(
    caplog, operation, failure
):
    upstream_url = "https://credentials.example.invalid/private?token=secret"
    activity_log = McpActivityLog()
    proxy = MCPProxyServerImpl(
        name="privacy-proxy",
        upstream_url=upstream_url,
        activity_log=activity_log,
    )
    exception = failure(f"failure contacting {upstream_url}")

    with (
        patch.object(proxy, "_connect_upstream", side_effect=exception),
        caplog.at_level(logging.ERROR, logger="pypost.core.mcp_proxy_server_impl"),
        pytest.raises(Exception),
    ):
        if operation == "list_tools":
            asyncio.run(proxy.list_tools())
        else:
            asyncio.run(proxy.call_tool("private-tool"))

    assert upstream_url not in caplog.text
    assert upstream_url not in str(activity_log.get_entries())
    assert activity_log.get_entries()[0].detail in {
        "Upstream request timed out",
        "Upstream connection failed",
        "Upstream operation failed",
    }


@pytest.mark.parametrize("operation", ["list_tools", "call_tool"])
def test_proxy_unresolved_variable_activity_is_sanitized(operation):
    activity_log = McpActivityLog()
    proxy = MCPProxyServerImpl(
        upstream_url="https://example.invalid/private?token=secret",
        headers={"Authorization": "Bearer {{ CREDENTIAL_NAME }}"},
        activity_log=activity_log,
    )

    with pytest.raises(McpUnresolvedVariableError):
        if operation == "list_tools":
            asyncio.run(proxy.list_tools())
        else:
            asyncio.run(proxy.call_tool("private-tool"))

    assert activity_log.get_entries()[0].detail == "Proxy variable could not be resolved"


class TestMcpProxyRegistryIntegration(unittest.TestCase):
    """Tests for MCPServerRegistry managing proxy server instances."""

    def test_registry_starts_proxy_server_without_collection(self):
        """MCPServerRegistry starts proxy server without requiring a collection."""
        registry = MCPServerRegistry()
        config = McpServerConfiguration(
            id="proxy-jira",
            name="Jira Proxy",
            port=2099,
            server_type="proxy",
            upstream_url="http://localhost:8080/mcp",
            upstream_transport="streamable_http",
            headers={"Authorization": "Bearer {{ JIRA_TOKEN }}"},
            environment_id="env-1",
            enabled=True,
        )
        registry.upsert(config)

        with patch.object(MCPServerManager, "start_proxy_server") as mock_start_proxy:
            registry.start("proxy-jira")
            mock_start_proxy.assert_called_once()

    def test_registry_reconciles_proxy_references_without_collection(self):
        """reconcile_references keeps proxy server enabled even if no collection matches."""
        registry = MCPServerRegistry()
        config = McpServerConfiguration(
            id="proxy-jira",
            port=2099,
            server_type="proxy",
            upstream_url="http://localhost:8080/mcp",
            headers={},
            environment_id="env-1",
            enabled=True,
        )
        registry.upsert(config)

        # Reconcile against an empty collection list
        changed = registry.reconcile_references(
            valid_collection_ids=set(),
            valid_environment_ids={"env-1"},
        )
        self.assertFalse(changed)
        saved_server = registry.get("proxy-jira")
        self.assertIsNotNone(saved_server)
        assert saved_server is not None
        self.assertTrue(saved_server.enabled)
