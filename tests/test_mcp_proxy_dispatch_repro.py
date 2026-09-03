"""Red repros for PYPOST-1102 shared proxy dispatch lifecycle."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from pypost.core.mcp_activity_log import McpActivityLog
from pypost.core.mcp_proxy_server_impl import MCPProxyServerImpl
from pypost.core.metrics_protocol import NullMetrics

pytestmark = pytest.mark.timeout(60)


def _proxy(*, activity_log: McpActivityLog | None = None) -> MCPProxyServerImpl:
    return MCPProxyServerImpl(
        name="dispatch-repro",
        upstream_url="http://upstream.invalid/mcp",
        activity_log=activity_log,
    )


def test_all_forwarded_methods_use_shared_dispatch_boundary() -> None:
    proxy = _proxy()
    dispatch = AsyncMock(side_effect=[[], MagicMock(), [], MagicMock(), [], MagicMock()])

    with patch.object(proxy, "_dispatch_proxy_operation", dispatch):
        asyncio.run(proxy.list_tools())
        asyncio.run(proxy.call_tool("tool", {"value": "x"}))
        asyncio.run(proxy.list_prompts())
        asyncio.run(proxy.get_prompt("prompt", {"value": "x"}))
        asyncio.run(proxy.list_resources())
        asyncio.run(proxy.read_resource("resource://one"))

    assert [call.args[0] for call in dispatch.await_args_list] == [
        "list_tools",
        "call_tool",
        "list_prompts",
        "get_prompt",
        "list_resources",
        "read_resource",
    ]


def test_shared_dispatch_maps_prompt_network_errors_and_records_lifecycle() -> None:
    activity_log = McpActivityLog()
    metrics = MagicMock(spec=NullMetrics)
    proxy = _proxy(activity_log=activity_log)
    proxy._metrics = metrics

    with patch.object(
        proxy,
        "_connect_upstream",
        side_effect=httpx.ConnectError("connection refused"),
    ):
        with pytest.raises(httpx.ConnectError, match="Connection failed"):
            asyncio.run(proxy.list_prompts())

    metrics.track_mcp_request_received.assert_called_once_with("POST")
    metrics.track_mcp_response_sent.assert_called_once_with("POST", "error")
    entry = activity_log.get_entries()[0]
    assert entry.operation == "list_prompts"
    assert entry.outcome == "error"
    assert entry.detail == "Upstream connection failed"
    assert entry.duration_ms is not None


def test_shared_dispatch_records_one_lifecycle_for_each_protocol_operation() -> None:
    activity_log = McpActivityLog()
    metrics = MagicMock(spec=NullMetrics)
    proxy = _proxy(activity_log=activity_log)
    proxy._metrics = metrics
    session = AsyncMock()
    session.list_tools.return_value = MagicMock(tools=[])
    session.call_tool.return_value = MagicMock(isError=False)
    session.list_prompts.return_value = MagicMock(prompts=[])
    session.get_prompt.return_value = MagicMock()
    session.list_resources.return_value = MagicMock(resources=[])
    session.read_resource.return_value = MagicMock()

    with patch.object(proxy, "_connect_upstream") as connect:
        connect.return_value.__aenter__.return_value = session
        asyncio.run(proxy.list_tools())
        asyncio.run(proxy.call_tool("tool"))
        asyncio.run(proxy.list_prompts())
        asyncio.run(proxy.get_prompt("prompt"))
        asyncio.run(proxy.list_resources())
        asyncio.run(proxy.read_resource("resource://one"))

    assert metrics.track_mcp_request_received.call_count == 6
    assert metrics.track_mcp_response_sent.call_count == 6
    metrics.track_mcp_tool_call_duration.assert_called_once()
    assert [entry.operation for entry in activity_log.get_entries()] == [
        "read_resource",
        "list_resources",
        "get_prompt",
        "list_prompts",
        "call_tool",
        "list_tools",
    ]
