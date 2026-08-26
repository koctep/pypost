"""Headless MCP Client draft presenter (PYPOST-1166 / MCP-TM-2).

Owns local Connect/Disconnect chrome state. Does not call MCPClientService
(live initialize is MCP-TM-3).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from pypost.models.mcp_client import McpClientConnection, McpClientSessionState

if TYPE_CHECKING:
    from pypost.ui.widgets.mcp_client.mcp_client_tab import McpClientTab

logger = logging.getLogger(__name__)

__all__ = ["McpClientPresenter"]


class McpClientPresenter:
    """Coordinates local MCP Client draft session state without a live SDK."""

    def __init__(self, connection: McpClientConnection) -> None:
        self.connection = connection
        self._tab: Optional[McpClientTab] = None
        self._state = McpClientSessionState.DISCONNECTED
        self._session: Optional[object] = None

    @property
    def state(self) -> McpClientSessionState:
        """Current local chrome session state."""
        return self._state

    def set_tab(self, tab: McpClientTab) -> None:
        """Bind the UI tab widget to this presenter."""
        self._tab = tab
        self._sync_ui()

    def connect_requested(self) -> None:
        """Update local state. Do not call MCPClientService (MCP-TM-3)."""
        logger.info(
            "mcp_client_connect_initiated connection_id=%s",
            self.connection.id,
        )
        self._sync_url_from_tab()
        self._session = object()
        self._state = McpClientSessionState.CONNECTED
        self._sync_ui()

    def disconnect_requested(self) -> None:
        """Return to disconnected chrome state and drop the local holder."""
        logger.info(
            "mcp_client_disconnect_initiated connection_id=%s",
            self.connection.id,
        )
        self._release_session()
        self._sync_ui()

    def teardown(self) -> None:
        """Release outbound session holder (no-op if none). Idempotent."""
        logger.info(
            "mcp_client_presenter_teardown connection_id=%s",
            self.connection.id,
        )
        self._release_session()
        self._sync_ui()

    def _release_session(self) -> None:
        self._session = None
        self._state = McpClientSessionState.DISCONNECTED

    def _sync_url_from_tab(self) -> None:
        if self._tab is None:
            return
        self.connection.url = self._tab.url_input.text()

    def _sync_ui(self) -> None:
        if self._tab is None:
            return
        self._tab.set_session_state(self._state)
