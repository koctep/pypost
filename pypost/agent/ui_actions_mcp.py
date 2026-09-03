"""Out-of-process stdio/HTTP MCP bridge for agent UI actions (PYPOST-990).

Dedicated MCP server wrapping ``pypost.agent.ui_actions`` via a duck-typed
``UiDriveSession`` (spawn ``AgentAppSession`` or attach client). Never mounted
on product ``MCPServerImpl``.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from pathlib import Path
import sys
import threading
from collections.abc import Callable
from typing import Any, Final, cast

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
import uvicorn
from PySide6.QtCore import QCoreApplication, QObject, QThread, Qt, Signal, Slot
from starlette.applications import Starlette

from pypost.agent.attach_ipc import AttachClientSession, AttachUnboundError
from pypost.agent.lifecycle import AgentAppSession
from pypost.agent.seed_loader import (
    DEFAULT_SEED_ENV_VAR,
    SeedLoadError,
    resolve_seed_path,
)
from pypost.agent.ui_actions import UiActionError
from pypost.agent.ui_drive import UiDriveSession
from pypost.core.mcp_streamable_http import build_streamable_http_route
from pypost.core.server_bind import drain_pending_tasks

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


def _process_events() -> None:
    app = QCoreApplication.instance()
    if app is not None:
        app.processEvents()


class QtMainThreadDispatcher(QObject):
    """Synchronously marshal a callable onto the Qt application thread."""

    requested = Signal(object)

    def __init__(self, timeout: float = 30.0) -> None:
        super().__init__()
        if QCoreApplication.instance() is None:
            raise RuntimeError("QtMainThreadDispatcher requires a Qt application")
        self._thread = QThread.currentThread()
        self._timeout = timeout
        self.requested.connect(self._run, Qt.ConnectionType.QueuedConnection)

    def dispatch(self, callback: Callable[[], Any]) -> Any:
        """Run ``callback`` on Qt's thread, waiting for its result."""
        if self.is_current_thread():
            return callback()

        completed = threading.Event()
        result: dict[str, Any] = {}
        self.requested.emit((callback, completed, result))
        if not completed.wait(self._timeout):
            raise TimeoutError(
                "Qt main-thread dispatch did not complete within "
                f"{self._timeout:.1f}s"
            )
        error = result.get("error")
        if isinstance(error, BaseException):
            raise error
        return result.get("value")

    def is_current_thread(self) -> bool:
        """Return whether the caller is running on the Qt application thread."""
        return QThread.currentThread() == self._thread

    @Slot(object)
    def _run(self, payload: object) -> None:
        callback, completed, result = cast(
            tuple[Callable[[], Any], threading.Event, dict[str, Any]], payload
        )
        try:
            result["value"] = callback()
        except BaseException as exc:
            result["error"] = exc
        finally:
            completed.set()


class AgentUiActionsMcpServer:
    """MCP tool catalog for agent UI drive — separate from product MCPServerImpl."""

    def __init__(
        self,
        session: UiDriveSession,
        *,
        dispatcher: QtMainThreadDispatcher | None = None,
    ) -> None:
        self._session = session
        self._dispatcher = dispatcher
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

    async def call_tool(
        self, name: str, arguments: dict[str, Any] | None
    ) -> list[TextContent]:
        if name not in AGENT_UI_MCP_TOOL_NAMES:
            raise ValueError(f"Tool {name} not found")
        args = arguments or {}
        logger.debug(
            "agent_ui_mcp_call_tool tool=%s widget_id=%s in_current_tab=%s",
            name,
            args.get("widget_id"),
            str(_bool_arg(args, "in_current_tab")).lower(),
        )
        if self._dispatcher is None or self._dispatcher.is_current_thread():
            _process_events()
        try:
            if self._dispatcher is None:
                self._dispatch_sync(name, args)
            else:
                self._dispatcher.dispatch(lambda: self._dispatch_sync(name, args))
        except (UiActionError, TimeoutError, ValueError) as exc:
            logger.info(
                "agent_ui_mcp_tool_failed tool=%s error=%s",
                name,
                type(exc).__name__,
            )
            payload = {"ok": False, "error": str(exc)}
            return [TextContent(type="text", text=json.dumps(payload))]
        finally:
            if self._dispatcher is None or self._dispatcher.is_current_thread():
                _process_events()
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


async def _serve_stdio(session: UiDriveSession) -> None:
    bridge = AgentUiActionsMcpServer(session)
    init_options = bridge.server.create_initialization_options()
    logger.info("agent_ui_mcp_stdio_listening server=%s", SERVER_NAME)
    async with stdio_server() as (read_stream, write_stream):
        await bridge.server.run(read_stream, write_stream, init_options)


def build_http_app(bridge: AgentUiActionsMcpServer) -> Starlette:
    """Build the optional agent-UI Streamable HTTP application."""
    mcp_route, lifespan = build_streamable_http_route(bridge.server)
    return Starlette(debug=False, routes=[mcp_route], lifespan=lifespan)


class AgentUiHttpServer:
    """Bounded Uvicorn lifecycle for the optional agent-UI HTTP entry."""

    def __init__(
        self,
        app: Starlette,
        *,
        host: str = "127.0.0.1",
        port: int = 0,
        startup_timeout: float = 30.0,
    ) -> None:
        self._app = app
        self._host = host
        self._port = port
        self._startup_timeout = startup_timeout
        self._resolved_port: int | None = None
        self._server: uvicorn.Server | None = None
        self._thread: threading.Thread | None = None
        self._ready = threading.Event()
        self._stopped = threading.Event()
        self._error: BaseException | None = None

    @property
    def endpoint(self) -> str:
        """Return the resolved Streamable HTTP MCP URL after startup."""
        if self._resolved_port is None:
            raise RuntimeError("AgentUiHttpServer has not started")
        return f"http://{self._host}:{self._resolved_port}/mcp"

    @property
    def is_running(self) -> bool:
        thread = self._thread
        return thread is not None and thread.is_alive()

    @property
    def error(self) -> BaseException | None:
        return self._error

    def start(self) -> None:
        """Start Uvicorn and wait for its listening socket or a failure."""
        if self._thread is not None:
            raise RuntimeError("AgentUiHttpServer already started")
        self._thread = threading.Thread(
            target=self._run,
            name="pypost-agent-ui-http",
            daemon=True,
        )
        logger.info(
            "agent_ui_mcp_http_starting host=%s port=%d",
            self._host,
            self._port,
        )
        self._thread.start()
        if not self._ready.wait(self._startup_timeout):
            self.stop()
            raise TimeoutError(
                "Agent UI MCP HTTP server did not become ready within "
                f"{self._startup_timeout:.1f}s"
            )
        if self._error is not None:
            error = self._error
            self.stop()
            raise RuntimeError("Agent UI MCP HTTP server failed to start") from error

    def stop(self) -> None:
        """Request shutdown and join the exact listener thread with a bound."""
        server = self._server
        if server is not None:
            server.should_exit = True
        thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=5.0)
        endpoint = (
            self.endpoint
            if self._resolved_port is not None
            else f"http://{self._host}:{self._port}/mcp"
        )
        if thread is not None and thread.is_alive():
            logger.error("agent_ui_mcp_http_stop_timeout endpoint=%s", endpoint)
        else:
            logger.info(
                "agent_ui_mcp_http_stopped endpoint=%s",
                endpoint,
            )

    def wait(self, timeout: float) -> None:
        """Wait for the listener thread while the caller pumps Qt events."""
        thread = self._thread
        if thread is not None:
            thread.join(timeout=timeout)

    def _run(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            config = uvicorn.Config(
                app=self._app,
                host=self._host,
                port=self._port,
                loop="asyncio",
                log_config=None,
                log_level="warning",
            )
            server = uvicorn.Server(config)
            server.install_signal_handlers = lambda: None
            self._server = server
            original_startup = server.startup

            async def startup_with_notify(sockets=None):
                await original_startup(sockets=sockets)
                sockets = server.servers
                if not sockets or not sockets[0].sockets:
                    raise RuntimeError("Agent UI MCP HTTP server has no listening socket")
                self._resolved_port = int(sockets[0].sockets[0].getsockname()[1])
                self._ready.set()
                logger.info(
                    "agent_ui_mcp_http_listening endpoint=%s",
                    self.endpoint,
                )

            setattr(server, "startup", startup_with_notify)
            loop.run_until_complete(server.serve())
        except BaseException as exc:
            self._error = exc
            self._ready.set()
            if not isinstance(exc, KeyboardInterrupt):
                logger.exception("agent_ui_mcp_http_failed")
        finally:
            drain_pending_tasks(loop)
            loop.close()
            self._stopped.set()


def main(argv: list[str] | None = None) -> None:
    """Serve UI-action MCP over stdio by default or optional Streamable HTTP."""
    parser = argparse.ArgumentParser(
        description="PyPost agent UI actions MCP sidecar (stdio or HTTP).",
    )
    parser.add_argument(
        "--http",
        action="store_true",
        help="Serve Streamable HTTP on /mcp instead of stdio (spawn mode only).",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="HTTP bind host when --http is selected (default: 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=0,
        help="HTTP bind port when --http is selected (default: 0/ephemeral).",
    )
    parser.add_argument(
        "--qt-dispatch-timeout",
        type=float,
        default=30.0,
        help="Seconds for an HTTP UI action to reach the Qt thread.",
    )
    parser.add_argument(
        "--attach",
        action="store_true",
        help=(
            "Bind to an already-running desktop attach host via local IPC "
            "(do not spawn AgentAppSession)."
        ),
    )
    parser.add_argument(
        "--attach-endpoint",
        default=None,
        help=(
            "AF_UNIX path for --attach (default: per-user well-known path "
            "or PYPOST_AGENT_UI_ATTACH_ENDPOINT)."
        ),
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
    parser.add_argument(
        "--seed",
        "--seed-file",
        dest="seed",
        default=None,
        help=(
            "Path to seed collection JSON/YAML file or seed data directory "
            f"(overrides {DEFAULT_SEED_ENV_VAR})."
        ),
    )
    parsed = parser.parse_args(argv)
    if parsed.attach and parsed.http:
        parser.error("--attach and --http cannot be combined")
    if parsed.port < 0 or parsed.port > 65535:
        parser.error("--port must be between 0 and 65535")
    if parsed.qt_dispatch_timeout <= 0:
        parser.error("--qt-dispatch-timeout must be greater than zero")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        stream=sys.stderr,
    )
    if parsed.attach:
        if parsed.seed is not None:
            logger.error(
                "agent_ui_mcp_attach_with_seed_rejected seed_path=%s "
                "error_type=%s error=%s",
                parsed.seed,
                "CommandLineError",
                "--attach cannot be combined with --seed",
            )
            sys.exit(1)
        _run_attach(parsed.attach_endpoint)
        return
    seed_path = resolve_seed_path(parsed.seed)
    spawn_kwargs: dict[str, Any] = {
        "offscreen": not parsed.no_offscreen,
        "ready_timeout": parsed.ready_timeout,
        "seed_path": seed_path,
    }
    if parsed.http:
        spawn_kwargs.update(
            {
                "http": True,
                "host": parsed.host,
                "port": parsed.port,
                "qt_dispatch_timeout": parsed.qt_dispatch_timeout,
            }
        )
    _run_spawn_session(
        **spawn_kwargs,
    )


def _run_attach(endpoint: str | None) -> None:
    """Connect to an existing UI attach server and serve MCP tools over stdio."""
    session = AttachClientSession(endpoint=endpoint)
    logger.info(
        "agent_ui_mcp_attach_starting endpoint=%s",
        session.endpoint,
    )
    try:
        session.connect()
    except AttachUnboundError as exc:
        logger.error(
            "agent_ui_mcp_attach_failed endpoint=%s error=%s",
            session.endpoint,
            type(exc).__name__,
        )
        raise SystemExit(1) from exc
    try:
        logger.info("agent_ui_mcp_attach_ready endpoint=%s", session.endpoint)
        asyncio.run(_serve_stdio(session))
    finally:
        session.detach()
        logger.info(
            "agent_ui_mcp_attach_ended endpoint=%s",
            session.endpoint,
        )


def _run_spawn_session(
    *,
    offscreen: bool,
    ready_timeout: float,
    seed_path: Path | None = None,
    http: bool = False,
    host: str = "127.0.0.1",
    port: int = 0,
    qt_dispatch_timeout: float = 30.0,
) -> None:
    """Spawn a session and serve MCP over the selected optional transport."""
    session = AgentAppSession(
        offscreen=offscreen,
        ready_timeout=ready_timeout,
        seed_path=seed_path,
    )
    http_server: AgentUiHttpServer | None = None
    try:
        session.start()
        logger.info(
            "agent_ui_mcp_session_ready offscreen=%s",
            str(offscreen).lower(),
        )
        if not http:
            asyncio.run(_serve_stdio(session))
        else:
            dispatcher = QtMainThreadDispatcher(timeout=qt_dispatch_timeout)
            bridge = AgentUiActionsMcpServer(session, dispatcher=dispatcher)
            http_server = AgentUiHttpServer(
                build_http_app(bridge),
                host=host,
                port=port,
                startup_timeout=ready_timeout,
            )
            http_server.start()
            while http_server.is_running:
                _process_events()
                http_server.wait(0.01)
    except SeedLoadError as exc:
        logger.error(
            "agent_ui_mcp_seed_failed seed_path=%s error_type=%s error=%s",
            seed_path,
            type(exc).__name__,
            exc,
        )
        sys.exit(1)
    finally:
        if http_server is not None:
            http_server.stop()
        session.shutdown()


if __name__ == "__main__":
    main()
