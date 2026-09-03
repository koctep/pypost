"""PYPOST-952: live out-of-process agent-UI MCP bridge (stdio sidecar)."""

from __future__ import annotations

import asyncio
import os
import re
import sys
import threading
from pathlib import Path
from threading import get_ident
from unittest.mock import MagicMock

import anyio
import pytest
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamable_http_client
from mcp.shared._httpx_utils import create_mcp_http_client
from starlette.routing import Route

from pypost.agent.ui_actions_mcp import (
    AGENT_UI_MCP_TOOL_NAMES,
    AgentUiActionsMcpServer,
    AgentUiHttpServer,
    QtMainThreadDispatcher,
    SERVER_NAME,
    build_http_app,
)
from pypost.core.mcp_transport_routes import MCP_STREAMABLE_HTTP_PATH

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


def test_cli_http_options_are_forwarded_to_spawn_session() -> None:
    """HTTP selection must be explicit and must not alter default stdio args."""
    from pypost.agent.ui_actions_mcp import main

    with pytest.MonkeyPatch.context() as monkeypatch:
        run_spawn = MagicMock()
        monkeypatch.setattr(
            "pypost.agent.ui_actions_mcp._run_spawn_session",
            run_spawn,
        )
        main(
            [
                "--http",
                "--host",
                "127.0.0.1",
                "--port",
                "8765",
                "--qt-dispatch-timeout",
                "4",
            ]
        )

    run_spawn.assert_called_once_with(
        offscreen=True,
        ready_timeout=30.0,
        seed_path=None,
        http=True,
        host="127.0.0.1",
        port=8765,
        qt_dispatch_timeout=4.0,
    )


def test_cli_rejects_http_attach_combination() -> None:
    """HTTP mode owns a spawned session and cannot be combined with attach."""
    from pypost.agent.ui_actions_mcp import main

    with pytest.raises(SystemExit) as exc_info:
        main(["--http", "--attach"])

    assert exc_info.value.code == 2


def test_mcpserver_impl_does_not_import_agent_ui_mcp_module() -> None:
    """Hard separation: product MCP impl must not import the UI bridge."""
    impl_path = _REPO_ROOT / "pypost" / "core" / "mcp_server_impl.py"
    text = impl_path.read_text(encoding="utf-8")
    if "ui_actions_mcp" in text:
        pytest.fail("mcp_server_impl.py must not reference ui_actions_mcp")


def test_http_app_exposes_shared_streamable_http_route(qapp) -> None:
    """Optional HTTP mode must publish the standard agent-UI /mcp route."""
    bridge = AgentUiActionsMcpServer(MagicMock())

    app = build_http_app(bridge)

    route_paths = [route.path for route in app.routes if isinstance(route, Route)]
    assert route_paths == [MCP_STREAMABLE_HTTP_PATH]


def test_http_call_tool_is_marshaled_to_qt_main_thread(qapp) -> None:
    """HTTP-worker calls must execute UI actions on the QApplication thread."""
    dispatcher = QtMainThreadDispatcher(timeout=2.0)
    session = MagicMock()
    session.ui_click.side_effect = lambda *_args, **_kwargs: session.call_thread(
        get_ident()
    )
    bridge = AgentUiActionsMcpServer(session, dispatcher=dispatcher)
    worker_error: list[BaseException] = []

    def invoke() -> None:
        try:
            anyio.run(
                bridge.call_tool,
                "ui_click",
                {"widget_id": "pypost_send_button"},
            )
        except BaseException as exc:  # pragma: no cover - assertion below reports it
            worker_error.append(exc)

    worker = threading.Thread(target=invoke)
    worker.start()
    while worker.is_alive():
        qapp.processEvents()
        worker.join(timeout=0.01)

    assert not worker_error
    session.call_thread.assert_called_once_with(get_ident())


@pytest.mark.slow
def test_http_sidecar_lists_and_calls_ui_tools(qapp) -> None:
    """A live Streamable HTTP client can discover and invoke the UI catalog."""
    dispatcher = QtMainThreadDispatcher(timeout=5.0)
    session = MagicMock()
    bridge = AgentUiActionsMcpServer(session, dispatcher=dispatcher)
    http_server = AgentUiHttpServer(build_http_app(bridge), port=0)

    async def _list_and_call() -> tuple[list[str], str]:
        async with create_mcp_http_client() as http_client:
            async with streamable_http_client(
                http_server.endpoint,
                http_client=http_client,
            ) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as client:
                    await client.initialize()
                    tools = await client.list_tools()
                    result = await client.call_tool(
                        "ui_click",
                        {"widget_id": "pypost_send_button"},
                    )
                    return [tool.name for tool in tools.tools], result.content[0].text

    result_box: dict[str, object] = {}

    def invoke() -> None:
        try:
            result_box["result"] = anyio.run(_list_and_call)
        except BaseException as exc:  # pragma: no cover - assertion below reports it
            result_box["error"] = exc

    worker = threading.Thread(target=invoke)
    try:
        http_server.start()
        worker.start()
        while worker.is_alive():
            qapp.processEvents()
            worker.join(timeout=0.01)
    finally:
        http_server.stop()

    assert "error" not in result_box
    names, payload = result_box["result"]
    assert set(names) == _EXPECTED_TOOLS
    assert payload == '{"ok": true}'
    session.ui_click.assert_called_once_with(
        "pypost_send_button",
        in_current_tab=False,
    )


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


@pytest.mark.agent_e2e
@pytest.mark.timeout(120)
def test_stdio_sidecar_calls_ui_click_and_fill() -> None:
    """Spawn sidecar subprocess; call_tool drives real click and fill widgets."""
    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "pypost.agent.ui_actions_mcp"],
        env=env,
    )

    async def _call_actions() -> tuple[str, str]:
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                with anyio.fail_after(20):
                    fill_result = await session.call_tool(
                        "ui_fill",
                        {
                            "widget_id": "pypost_url_input",
                            "text": "https://agent-ui.example/",
                            "in_current_tab": True,
                        },
                    )
                with anyio.fail_after(20):
                    click_result = await session.call_tool(
                        "ui_click",
                        {
                            "widget_id": "pypost_url_input",
                            "in_current_tab": True,
                        },
                    )
                return (
                    fill_result.content[0].text,
                    click_result.content[0].text,
                )

    fill_text, click_text = anyio.run(_call_actions)
    assert fill_text == '{"ok": true}'
    assert click_text == '{"ok": true}'
