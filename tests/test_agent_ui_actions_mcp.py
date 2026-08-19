"""PYPOST-952: live out-of-process agent-UI MCP bridge (stdio sidecar)."""

from __future__ import annotations

import asyncio
import os
import re
import sys
from pathlib import Path

import anyio
import pytest
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from pypost.agent.ui_actions_mcp import (
    AGENT_UI_MCP_TOOL_NAMES,
    SERVER_NAME,
)

pytestmark = pytest.mark.timeout(60)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_PYPROJECT = _REPO_ROOT / "pyproject.toml"
_ENTRY_SCRIPT = "pypost-agent-ui-mcp"
_EXPECTED_TOOLS = frozenset(
    {"ui_click", "ui_fill", "ui_select", "ui_send_key"},
)


def test_agent_ui_mcp_module_exports_tool_names() -> None:
    """Dedicated bridge must expose the four ui_actions tool names."""
    assert AGENT_UI_MCP_TOOL_NAMES == _EXPECTED_TOOLS


def test_agent_ui_mcp_server_name_is_distinct_from_product() -> None:
    """Sidecar server name must differ from default product MCP server."""
    assert SERVER_NAME != "pypost-server"
    assert "agent" in SERVER_NAME.lower()


def test_pyproject_declares_agent_ui_mcp_console_script() -> None:
    """Packaging entry must be declared for pip install / PATH."""
    text = _PYPROJECT.read_text(encoding="utf-8")
    pattern = rf'^\s*{_ENTRY_SCRIPT}\s*=\s*"pypost\.agent\.ui_actions_mcp:main"\s*$'
    if not re.search(pattern, text, flags=re.MULTILINE):
        pytest.fail(
            f"Missing [project.scripts] entry {_ENTRY_SCRIPT!r} in pyproject.toml"
        )


def test_mcpserver_impl_does_not_import_agent_ui_mcp_module() -> None:
    """Hard separation: product MCP impl must not import the UI bridge."""
    impl_path = _REPO_ROOT / "pypost" / "core" / "mcp_server_impl.py"
    text = impl_path.read_text(encoding="utf-8")
    if "ui_actions_mcp" in text:
        pytest.fail("mcp_server_impl.py must not reference ui_actions_mcp")


@pytest.mark.agent_e2e
@pytest.mark.timeout(120)
def test_stdio_sidecar_lists_ui_action_tools() -> None:
    """Spawn sidecar subprocess; list_tools returns the four UI primitives."""
    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "pypost.agent.ui_actions_mcp"],
        env=env,
    )

    async def _list() -> list[str]:
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.list_tools()
                return [tool.name for tool in result.tools]

    names = anyio.run(_list)
    assert set(names) == _EXPECTED_TOOLS
