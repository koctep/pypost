"""Popup protocol picker for blank workspace tabs (PYPOST-1157)."""

from __future__ import annotations

from enum import Enum

from PySide6.QtCore import QPoint
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QMenu, QPushButton, QWidget

from pypost.ui.widget_ids import NEW_TAB_PROTOCOL_MENU, PLUS_TAB_BUTTON, set_widget_id


class TabProtocol(str, Enum):
    """Blank-tab protocol choice; values match metrics ``protocol`` labels."""

    HTTP = "http"
    WEBSOCKET = "websocket"
    MCP_CLIENT = "mcp_client"


def _anchor_point(parent: QWidget | None) -> QPoint:
    if parent is not None:
        plus_btn = parent.findChild(QPushButton, PLUS_TAB_BUTTON)
        if plus_btn is not None:
            return plus_btn.mapToGlobal(plus_btn.rect().bottomLeft())
    return QCursor.pos()


class NewTabProtocolPicker:
    """Option A QMenu: HTTP Request first (default), then WebSocket, then MCP Client."""

    def build_menu(self, parent: QWidget | None = None) -> QMenu:
        menu = QMenu(parent)
        set_widget_id(menu, NEW_TAB_PROTOCOL_MENU)
        http_action = menu.addAction("HTTP Request")
        http_action.setData(TabProtocol.HTTP)
        websocket_action = menu.addAction("WebSocket")
        websocket_action.setData(TabProtocol.WEBSOCKET)
        mcp_action = menu.addAction("MCP Client")
        mcp_action.setData(TabProtocol.MCP_CLIENT)
        menu.setActiveAction(http_action)
        return menu

    def prompt(
        self,
        parent: QWidget | None = None,
        *,
        anchor: QPoint | None = None,
    ) -> TabProtocol | None:
        """Return the chosen protocol, or None if the menu was dismissed."""
        menu = self.build_menu(parent)
        http_action = menu.actions()[0]
        pos = anchor if anchor is not None else _anchor_point(parent)
        chosen = menu.exec(pos, http_action)
        if chosen is None:
            return None
        data = chosen.data()
        if data is None:
            return None
        try:
            return TabProtocol(data)
        except ValueError:
            return None
