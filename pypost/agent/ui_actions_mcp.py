"""Out-of-process stdio MCP bridge for agent UI actions (PYPOST-952).

Dedicated MCP server wrapping ``pypost.agent.ui_actions`` via ``AgentAppSession``.
Never mounted on product ``MCPServerImpl``.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from typing import Any, Final

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from PySide6.QtCore import QCoreApplication, Qt

from pypost.agent.lifecycle import AgentAppSession
from pypost.agent.ui_actions import UiActionError

logger = logging.getLogger(__name__)

SERVER_NAME: Final = "pypost-agent-ui"
AGENT_UI_MCP_TOOL_NAMES: Final[frozenset[str]] = frozenset(
    {
        "ui_click",
        "ui_fill",
        "ui_select",
        "ui_send_key",
    }
)

_WIDGET_ID_SCHEMA: Final[dict[str, Any]] = {
    "type": "object",
    "properties": {
        "widget_id": {
            "type": "string",
            "description": "Stable objectName / widget id under the lookup root.",
        },
        "in_current_tab": {
            "type": "boolean",
            "description": (
                "When true, resolve widget_id under the active request tab "
                "instead of the main window."
            ),
        },
    },
    "required": ["widget_id"],
}

_MODIFIER_NAMES: Final[dict[str, Qt.KeyboardModifier]] = {
    "control": Qt.KeyboardModifier.ControlModifier,
    "ctrl": Qt.KeyboardModifier.ControlModifier,
    "shift": Qt.KeyboardModifier.ShiftModifier,
    "alt": Qt.KeyboardModifier.AltModifier,
    "meta": Qt.KeyboardModifier.MetaModifier,
}


def _tool_schemas() -> dict[str, dict[str, Any]]:
    click = {
        **_WIDGET_ID_SCHEMA,
        "additionalProperties": False,
    }
    fill = {
        "type": "object",
        "properties": {
            **_WIDGET_ID_SCHEMA["properties"],
            "text": {"type": "string", "description": "Text to set or type."},
            "via_key_clicks": {
                "type": "boolean",
                "description": "Use QTest.keyClicks instead of setters.",
            },
            "delay": {
                "type": "integer",
                "description": "Milliseconds between keys when via_key_clicks.",
            },
        },
        "required": ["widget_id", "text"],
        "additionalProperties": False,
    }
    select = {
        "type": "object",
        "properties": {
            **_WIDGET_ID_SCHEMA["properties"],
            "option": {
                "type": "string",
                "description": "Display text to select (exact match).",
            },
            "option_index": {
                "type": "integer",
                "description": "Zero-based index to select.",
            },
        },
        "required": ["widget_id"],
        "additionalProperties": False,
    }
    send_key = {
        "type": "object",
        "properties": {
            **_WIDGET_ID_SCHEMA["properties"],
            "key": {
                "type": "string",
                "description": "Key name (e.g. return, a) or Qt.Key suffix.",
            },
            "modifiers": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional modifier names: control, shift, alt, meta.",
            },
        },
        "required": ["widget_id", "key"],
        "additionalProperties": False,
    }
    return {
        "ui_click": click,
        "ui_fill": fill,
        "ui_select": select,
        "ui_send_key": send_key,
    }


def _parse_modifiers(values: list[str] | None) -> Qt.KeyboardModifier:
    mods = Qt.KeyboardModifier.NoModifier
    for raw in values or []:
        name = raw.lower().strip()
        modifier = _MODIFIER_NAMES.get(name)
        if modifier is None:
            raise ValueError(f"Unknown modifier: {raw!r}")
        mods |= modifier
    return mods


def _bool_arg(arguments: dict[str, Any], key: str, default: bool = False) -> bool:
    value = arguments.get(key, default)
    return bool(value)


class AgentUiActionsMcpServer:
    """MCP tool catalog for agent UI drive — separate from product MCPServerImpl."""

    def __init__(self, session: AgentAppSession) -> None:
        self._session = session
        self._schemas = _tool_schemas()
        self.server = Server(SERVER_NAME)
        self.server.list_tools()(self.list_tools)
        self.server.call_tool()(self.call_tool)

    async def list_tools(self) -> list[Tool]:
        descriptions = {
            "ui_click": "Left-click a named widget.",
            "ui_fill": "Fill a text input (setters or optional keyClicks).",
            "ui_select": "Select combo/list/tree option by text or index.",
            "ui_send_key": "Send a key or hotkey to a named widget.",
        }
        return [
            Tool(
                name=name,
                description=descriptions[name],
                inputSchema=self._schemas[name],
            )
            for name in sorted(AGENT_UI_MCP_TOOL_NAMES)
        ]

    async def call_tool(self, name: str, arguments: dict[str, Any] | None) -> list[TextContent]:
        if name not in AGENT_UI_MCP_TOOL_NAMES:
            raise ValueError(f"Tool {name} not found")
        args = arguments or {}
        logger.debug(
            "agent_ui_mcp_call_tool tool=%s widget_id=%s in_current_tab=%s",
            name,
            args.get("widget_id"),
            str(_bool_arg(args, "in_current_tab")).lower(),
        )
        QCoreApplication.processEvents()
        try:
            self._dispatch_sync(name, args)
        except UiActionError as exc:
            logger.info(
                "agent_ui_mcp_tool_failed tool=%s error=%s",
                name,
                type(exc).__name__,
            )
            payload = {"ok": False, "error": str(exc)}
            return [TextContent(type="text", text=json.dumps(payload))]
        except ValueError as exc:
            payload = {"ok": False, "error": str(exc)}
            return [TextContent(type="text", text=json.dumps(payload))]
        finally:
            QCoreApplication.processEvents()
        return [TextContent(type="text", text=json.dumps({"ok": True}))]

    def _dispatch_sync(self, name: str, args: dict[str, Any]) -> None:
        in_tab = _bool_arg(args, "in_current_tab")
        widget_id = args["widget_id"]
        if name == "ui_click":
            self._session.ui_click(widget_id, in_current_tab=in_tab)
            return
        if name == "ui_fill":
            self._session.ui_fill(
                widget_id,
                args["text"],
                in_current_tab=in_tab,
                via_key_clicks=_bool_arg(args, "via_key_clicks"),
                delay=int(args.get("delay", -1)),
            )
            return
        if name == "ui_select":
            if "option" in args and "option_index" in args:
                raise ValueError("Provide option or option_index, not both")
            if "option" in args:
                self._session.ui_select(
                    widget_id, args["option"], in_current_tab=in_tab
                )
                return
            if "option_index" in args:
                self._session.ui_select(
                    widget_id, int(args["option_index"]), in_current_tab=in_tab
                )
                return
            raise ValueError("ui_select requires option or option_index")
        if name == "ui_send_key":
            modifiers = _parse_modifiers(args.get("modifiers"))
            self._session.ui_send_key(
                widget_id,
                args["key"],
                modifiers=modifiers,
                in_current_tab=in_tab,
            )
            return
        raise ValueError(f"Unhandled tool: {name}")


async def _serve_stdio(session: AgentAppSession) -> None:
    bridge = AgentUiActionsMcpServer(session)
    init_options = bridge.server.create_initialization_options()
    logger.info("agent_ui_mcp_stdio_listening server=%s", SERVER_NAME)
    async with stdio_server() as (read_stream, write_stream):
        await bridge.server.run(read_stream, write_stream, init_options)


def main(argv: list[str] | None = None) -> None:
    """Launch AgentAppSession and serve UI-action MCP over stdio."""
    parser = argparse.ArgumentParser(
        description="PyPost agent UI actions MCP sidecar (stdio; PYPOST-952).",
    )
    parser.add_argument(
        "--no-offscreen",
        action="store_true",
        help="Do not force QT_QPA_PLATFORM=offscreen (default: offscreen).",
    )
    parser.add_argument(
        "--ready-timeout",
        type=float,
        default=30.0,
        help="Seconds to wait for MainWindow.is_ui_ready (default: 30).",
    )
    parsed = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        stream=sys.stderr,
    )
    session = AgentAppSession(
        offscreen=not parsed.no_offscreen,
        ready_timeout=parsed.ready_timeout,
    )
    try:
        session.start()
        logger.info(
            "agent_ui_mcp_session_ready offscreen=%s",
            str(not parsed.no_offscreen).lower(),
        )
        asyncio.run(_serve_stdio(session))
    finally:
        session.shutdown()


if __name__ == "__main__":
    main()
