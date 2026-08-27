"""WebSocket and MCP Client session hotkey registration for MainWindow."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pypost.ui.hotkeys import register_hotkey, register_hotkey_documentation

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

    from pypost.ui.presenters.tabs_presenter import TabsPresenter


def register_protocol_session_hotkeys(
    parent: QWidget,
    tabs: TabsPresenter,
) -> None:
    """Register WebSocket Session and MCP Client help rows and WS Format JSON."""
    register_hotkey_documentation(
        parent,
        section="WebSocket Session",
        label="Connect / Disconnect",
        keys=("F5", "Ctrl+Return"),
        order=1,
    )
    register_hotkey_documentation(
        parent,
        section="WebSocket Session",
        label="Send Message",
        keys=("Ctrl+Return",),
        order=2,
    )
    register_hotkey_documentation(
        parent,
        section="WebSocket Session",
        label="Focus URL Bar",
        keys=("Ctrl+L", "Alt+D"),
        order=4,
    )
    register_hotkey(
        parent,
        section="WebSocket Session",
        label="Format JSON",
        keys=("Ctrl+Shift+F",),
        slot=tabs.handle_websocket_format_json_global,
        order=5,
    )
    register_hotkey_documentation(
        parent,
        section="MCP Client",
        label="Connect / Disconnect",
        keys=("F5", "Ctrl+Return"),
        order=1,
    )
    register_hotkey_documentation(
        parent,
        section="MCP Client",
        label="Invoke Tool",
        keys=("Ctrl+Return",),
        order=2,
    )
    register_hotkey_documentation(
        parent,
        section="MCP Client",
        label="Focus URL Bar",
        keys=("Ctrl+L", "Alt+D"),
        order=4,
    )
