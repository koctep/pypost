"""MCP Client draft presenter (PYPOST-1166 / PYPOST-1167).

Owns local Connect/Disconnect chrome and header-aware outbound execute.
Connect does not call MCPClientService (live initialize is MCP-TM-3).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional

from pypost.core.template_service import TemplateService
from pypost.models.mcp_client import McpClientConnection, McpClientSessionState
from pypost.models.response import ResponseData

if TYPE_CHECKING:
    from pypost.core.mcp_client_service import MCPClientService
    from pypost.ui.widgets.mcp_client.mcp_client_tab import McpClientTab

logger = logging.getLogger(__name__)

__all__ = ["McpClientPresenter"]


class McpClientPresenter:
    """Coordinates MCP Client chrome, environment resolve, and outbound calls."""

    def __init__(
        self,
        connection: McpClientConnection,
        env_vars: dict[str, str] | None = None,
        hidden_keys: set[str] | None = None,
        template_service: TemplateService | None = None,
        mcp_client: MCPClientService | None = None,
    ) -> None:
        self.connection = connection
        self._tab: Optional[McpClientTab] = None
        self._state = McpClientSessionState.DISCONNECTED
        self._session: Optional[object] = None
        self._env_vars: dict[str, str] = dict(env_vars or {})
        self._hidden_keys: set[str] = set(hidden_keys or set())
        self._template_service = template_service or TemplateService()
        self._mcp_client = mcp_client

    @property
    def state(self) -> McpClientSessionState:
        """Current local chrome session state."""
        return self._state

    def set_tab(self, tab: McpClientTab) -> None:
        """Bind the UI tab widget to this presenter."""
        self._tab = tab
        self._propagate_variables_to_tab()
        self._sync_ui()

    def set_variables(self, variables: dict[str, str]) -> None:
        """Update the active environment snapshot and fan it out to chrome."""
        self._env_vars = dict(variables)
        self._propagate_variables_to_tab()

    def set_hidden_keys(self, hidden_keys: set[str]) -> None:
        """Update hidden environment keys and fan them out to chrome."""
        self._hidden_keys = set(hidden_keys)
        self._propagate_variables_to_tab()

    def resolve_outbound_fields(self) -> tuple[str, dict[str, str]]:
        """Render URL and header names/values from the active environment."""
        self._sync_fields_from_tab()
        variables = self._env_vars
        resolved_url = self._template_service.render_string(
            self.connection.url,
            variables,
        )
        raw_headers = dict(self.connection.headers)
        resolved_headers = {
            self._template_service.render_string(key, variables): (
                self._template_service.render_string(value, variables)
            )
            for key, value in raw_headers.items()
        }
        logger.debug(
            "mcp_client_outbound_fields_resolved connection_id=%s header_count=%d",
            self.connection.id,
            len(resolved_headers),
        )
        return resolved_url, resolved_headers

    def execute_outbound(
        self,
        operation: str,
        call_params: dict[str, Any] | None = None,
    ) -> ResponseData:
        """Call MCPClientService.run with environment-resolved URL and headers."""
        resolved_url, resolved_headers = self.resolve_outbound_fields()
        return self._client().run(
            resolved_url,
            operation,
            call_params,
            headers=resolved_headers,
        )

    def connect_requested(self) -> None:
        """Update local state. Do not call MCPClientService (MCP-TM-3)."""
        logger.info(
            "mcp_client_connect_initiated connection_id=%s",
            self.connection.id,
        )
        self._sync_fields_from_tab()
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

    def _client(self) -> MCPClientService:
        if self._mcp_client is None:
            from pypost.core.mcp_client_service import MCPClientService

            self._mcp_client = MCPClientService()
        return self._mcp_client

    def _release_session(self) -> None:
        self._session = None
        self._state = McpClientSessionState.DISCONNECTED

    def _sync_fields_from_tab(self) -> None:
        if self._tab is None:
            return
        self.connection.url = self._tab.url_input.text()
        self.connection.headers = self._tab.headers_data()

    def _propagate_variables_to_tab(self) -> None:
        if self._tab is None:
            return
        self._tab.set_variables(self._env_vars)
        self._tab.set_hidden_keys(self._hidden_keys)

    def _sync_ui(self) -> None:
        if self._tab is None:
            return
        self._tab.set_session_state(self._state)
