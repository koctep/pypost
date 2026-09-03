"""Process-based MCP proxy wire tests for PYPOST-1105."""
from __future__ import annotations

import multiprocessing
from contextlib import contextmanager
from typing import Any, Iterator

import anyio
import pytest
import uvicorn
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.server import Server
from mcp.shared._httpx_utils import create_mcp_http_client
from mcp.types import TextContent, Tool
from starlette.applications import Starlette
from starlette.routing import Mount

from pypost.core.mcp_legacy_sse import build_legacy_sse_app
from pypost.core.mcp_proxy_server_impl import MCPProxyServerImpl
from pypost.core.mcp_streamable_http import build_streamable_http_route
from pypost.core.mcp_transport_routes import MCP_LEGACY_SSE_MOUNT_PATH
from tests.helpers.mcp_live_server import free_port, wait_for_port

pytestmark = [pytest.mark.timeout(120), pytest.mark.slow]

_WIRE_TOOL_NAME = "wire_echo"
_LARGE_WIRE_PAYLOAD = "wire-chunk-start:" + ("payload-" * 16384) + ":wire-chunk-end"


def _build_upstream_app() -> Starlette:
    server = Server("wire-upstream")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name=_WIRE_TOOL_NAME,
                description="Return a deterministic wire payload",
                inputSchema={"type": "object", "properties": {}},
            )
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        del arguments
        if name != _WIRE_TOOL_NAME:
            return [TextContent(type="text", text="unknown tool")]
        return [TextContent(type="text", text=_LARGE_WIRE_PAYLOAD)]

    mcp_route, lifespan = build_streamable_http_route(server)
    return Starlette(
        debug=False,
        routes=[
            mcp_route,
            Mount(MCP_LEGACY_SSE_MOUNT_PATH, app=build_legacy_sse_app(server)),
        ],
        lifespan=lifespan,
    )


def _run_server_process(
    port: int,
    role: str,
    upstream_url: str,
    upstream_transport: str,
) -> None:
    if role == "upstream":
        app = _build_upstream_app()
    else:
        app = MCPProxyServerImpl(
            name="wire-proxy",
            upstream_url=upstream_url,
            upstream_transport=upstream_transport,
            timeout=15.0,
        ).create_app()

    config = uvicorn.Config(
        app=app,
        host="127.0.0.1",
        port=port,
        loop="asyncio",
        log_config=None,
        log_level="warning",
    )
    server = uvicorn.Server(config)
    server.install_signal_handlers = lambda: None
    server.run()


class LiveMCPProcess:
    """Own one isolated Uvicorn process used by the wire tests."""

    def __init__(
        self,
        role: str,
        *,
        upstream_url: str = "",
        upstream_transport: str = "streamable_http",
    ) -> None:
        self.port = free_port()
        context = multiprocessing.get_context("spawn")
        self._process = context.Process(
            target=_run_server_process,
            args=(self.port, role, upstream_url, upstream_transport),
            daemon=True,
        )

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    @property
    def mcp_url(self) -> str:
        return f"{self.base_url}/mcp"

    @property
    def sse_url(self) -> str:
        return f"{self.base_url}{MCP_LEGACY_SSE_MOUNT_PATH}/"

    def start(self) -> None:
        self._process.start()
        wait_for_port("127.0.0.1", self.port, timeout=15.0)
        if not self._process.is_alive():
            raise RuntimeError("MCP process exited before becoming ready")

    def stop(self) -> None:
        if self._process.is_alive():
            self._process.terminate()
        self._process.join(timeout=5.0)
        if self._process.is_alive():
            self._process.kill()
            self._process.join(timeout=5.0)


@contextmanager
def live_mcp_process(
    role: str,
    *,
    upstream_url: str = "",
    upstream_transport: str = "streamable_http",
) -> Iterator[LiveMCPProcess]:
    process = LiveMCPProcess(
        role,
        upstream_url=upstream_url,
        upstream_transport=upstream_transport,
    )
    process.start()
    try:
        yield process
    finally:
        process.stop()


async def _list_and_call(mcp_url: str) -> tuple[list[str], str]:
    async with create_mcp_http_client() as http_client:
        async with streamable_http_client(mcp_url, http_client=http_client) as (
            read_stream,
            write_stream,
            _,
        ):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools = await session.list_tools()
                result = await session.call_tool(_WIRE_TOOL_NAME, {})
                return [tool.name for tool in tools.tools], result.content[0].text


def test_streamable_http_proxy_forwards_large_wire_payload() -> None:
    """A process-separated proxy forwards a large Streamable HTTP response."""
    with live_mcp_process("upstream") as upstream:
        with live_mcp_process(
            "proxy",
            upstream_url=upstream.mcp_url,
            upstream_transport="streamable_http",
        ) as proxy:
            names, payload = anyio.run(_list_and_call, proxy.mcp_url)

    assert names == [_WIRE_TOOL_NAME]
    assert payload == _LARGE_WIRE_PAYLOAD
    assert len(payload) > 100_000


def test_legacy_sse_proxy_forwards_real_event_stream() -> None:
    """A process-separated proxy forwards a tool call over an SSE upstream."""
    with live_mcp_process("upstream") as upstream:
        with live_mcp_process(
            "proxy",
            upstream_url=upstream.sse_url,
            upstream_transport="sse",
        ) as proxy:
            names, payload = anyio.run(_list_and_call, proxy.mcp_url)

    assert names == [_WIRE_TOOL_NAME]
    assert payload == _LARGE_WIRE_PAYLOAD
