"""MCP Client draft presenter (PYPOST-1166 / PYPOST-1167 / PYPOST-1169).

Owns Connect/Disconnect/Refresh chrome. Resolve URL/headers on the GUI
thread; list_tools runs on a presenter-owned worker via MCPClientService.run.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any, Optional

from PySide6.QtCore import QObject, Slot

from pypost.core.metrics_protocol import MetricsTrackerProtocol, resolve_metrics
from pypost.core.sensitive_text_sanitizer import sanitize_text
from pypost.core.template_service import TemplateService
from pypost.models.errors import ExecutionError
from pypost.models.mcp_client import McpClientConnection, McpClientSessionState
from pypost.models.response import ResponseData
from pypost.ui.presenters.mcp_client_worker import McpClientOutboundWorker

if TYPE_CHECKING:
    from pypost.core.mcp_client_service import MCPClientService
    from pypost.ui.widgets.mcp_client.mcp_client_tab import McpClientTab

logger = logging.getLogger(__name__)

__all__ = ["McpClientPresenter"]

_EMPTY_URL_MESSAGE = "Enter a server URL."
_INVALID_TOOLS_MESSAGE = "MCP server returned an invalid tools list."
_REFRESH_PROGRESS = "Refreshing tools..."
_KIND_CONNECT = "connect"
_KIND_REFRESH = "refresh"


class _ListResultBridge(QObject):
    """Deliver worker results onto the GUI thread (QueuedConnection)."""

    def __init__(self, presenter: McpClientPresenter) -> None:
        super().__init__()
        self._presenter = presenter

    @Slot(int, str, object)
    def on_ok(self, generation: int, kind: str, response: object) -> None:
        self._presenter._on_list_ok(generation, kind, response)

    @Slot(int, str, object)
    def on_error(self, generation: int, kind: str, error: object) -> None:
        self._presenter._on_list_error(generation, kind, error)


class McpClientPresenter:
    """Coordinates MCP Client chrome, environment resolve, and outbound calls."""

    def __init__(
        self,
        connection: McpClientConnection,
        env_vars: dict[str, str] | None = None,
        hidden_keys: set[str] | None = None,
        template_service: TemplateService | None = None,
        mcp_client: MCPClientService | None = None,
        metrics: MetricsTrackerProtocol | None = None,
    ) -> None:
        self.connection = connection
        self._tab: Optional[McpClientTab] = None
        self._state = McpClientSessionState.DISCONNECTED
        self._session: Optional[object] = None
        self._env_vars: dict[str, str] = dict(env_vars or {})
        self._hidden_keys: set[str] = set(hidden_keys or set())
        self._template_service = template_service or TemplateService()
        self._mcp_client = mcp_client
        self._metrics = resolve_metrics(metrics)
        self._list_in_flight = False
        self._outbound_generation = 0
        self._error_text = ""
        self._progress_text = ""
        self._worker: McpClientOutboundWorker | None = None
        self._bridge: _ListResultBridge | None = None

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
        """Resolve on the GUI thread and start list_tools (kind=connect)."""
        logger.info(
            "mcp_client_connect_initiated connection_id=%s",
            self.connection.id,
        )
        if self._list_in_flight:
            return
        if self._state == McpClientSessionState.CONNECTED:
            return
        self._start_list(_KIND_CONNECT)

    def refresh_requested(self) -> None:
        """Re-list tools while staying CONNECTED (kind=refresh)."""
        logger.info(
            "mcp_client_refresh_initiated connection_id=%s",
            self.connection.id,
        )
        if self._list_in_flight:
            return
        if self._state != McpClientSessionState.CONNECTED:
            return
        self._start_list(_KIND_REFRESH)

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

    def _ensure_bridge(self) -> _ListResultBridge:
        if self._bridge is None:
            self._bridge = _ListResultBridge(self)
        return self._bridge

    def _start_list(self, kind: str) -> None:
        resolved_url, resolved_headers = self.resolve_outbound_fields()
        if not resolved_url.strip():
            logger.warning(
                "mcp_client_list_rejected connection_id=%s kind=%s reason=empty_url",
                self.connection.id,
                kind,
            )
            if kind == _KIND_REFRESH:
                self._apply_refresh_failure(_EMPTY_URL_MESSAGE)
            else:
                self._apply_connect_failure(_EMPTY_URL_MESSAGE)
            return
        self._outbound_generation += 1
        generation = self._outbound_generation
        self._list_in_flight = True
        self._error_text = ""
        if kind == _KIND_CONNECT:
            self._session = None
            self._state = McpClientSessionState.CONNECTING
            self._progress_text = ""
            if self._tab is not None:
                self._tab.clear_tools()
        else:
            self._progress_text = _REFRESH_PROGRESS
        self._sync_ui()
        self._drop_worker()
        worker = McpClientOutboundWorker(
            self._client(),
            resolved_url,
            resolved_headers,
            "list_tools",
            None,
            generation,
            kind,
        )
        bridge = self._ensure_bridge()
        worker.finished_ok.connect(bridge.on_ok)
        worker.finished_error.connect(bridge.on_error)
        self._worker = worker
        worker.start()

    def _on_list_ok(
        self,
        generation: int,
        kind: str,
        response: object,
    ) -> None:
        if generation != self._outbound_generation:
            logger.debug(
                "mcp_client_list_tools_ignored connection_id=%s kind=%s",
                self.connection.id,
                kind,
            )
            return
        self._list_in_flight = False
        self._progress_text = ""
        tools = self._parse_tools(response)
        if tools is None:
            logger.error(
                "mcp_client_list_tools_failed connection_id=%s kind=%s "
                "reason=invalid_tools",
                self.connection.id,
                kind,
            )
            self._finish_list_failure(kind, _INVALID_TOOLS_MESSAGE)
            self._drop_worker()
            return
        logger.info(
            "mcp_client_list_tools_succeeded connection_id=%s kind=%s tool_count=%d",
            self.connection.id,
            kind,
            len(tools),
        )
        if self._tab is not None:
            self._tab.set_tools(tools)
        self._session = object()
        self._state = McpClientSessionState.CONNECTED
        self._error_text = ""
        self._sync_ui()
        self._record_list_outcome(kind, "success")
        self._drop_worker()

    def _on_list_error(
        self,
        generation: int,
        kind: str,
        error: object,
    ) -> None:
        if generation != self._outbound_generation:
            logger.debug(
                "mcp_client_list_tools_ignored connection_id=%s kind=%s",
                self.connection.id,
                kind,
            )
            return
        self._list_in_flight = False
        self._progress_text = ""
        message = (
            error.message
            if isinstance(error, ExecutionError)
            else str(error)
        )
        logger.error(
            "mcp_client_list_tools_failed connection_id=%s kind=%s",
            self.connection.id,
            kind,
        )
        self._finish_list_failure(kind, message)
        self._drop_worker()

    def _finish_list_failure(self, kind: str, message: str) -> None:
        if kind == _KIND_REFRESH:
            self._apply_refresh_failure(message)
        else:
            self._apply_connect_failure(message)

    def _apply_connect_failure(self, message: str) -> None:
        self._list_in_flight = False
        self._progress_text = ""
        self._session = None
        self._state = McpClientSessionState.FAILED
        self._error_text = self._sanitize(message)
        if self._tab is not None:
            self._tab.clear_tools()
        self._sync_ui()
        self._record_list_outcome(_KIND_CONNECT, "error")

    def _apply_refresh_failure(self, message: str) -> None:
        self._list_in_flight = False
        self._progress_text = ""
        self._error_text = self._sanitize(message)
        self._sync_ui()
        self._record_list_outcome(_KIND_REFRESH, "error")

    def _record_list_outcome(self, kind: str, result: str) -> None:
        """Increment outbound Connect / list_tools counters. No URL or headers."""
        if kind == _KIND_CONNECT:
            self._metrics.track_mcp_client_connect(result)
        self._metrics.track_mcp_client_list_tools(result, kind)

    def _sanitize(self, message: str) -> str:
        return sanitize_text(
            message,
            env_vars=self._env_vars,
            hidden_keys=self._hidden_keys,
        )

    def _parse_tools(
        self,
        response: object,
    ) -> list[tuple[str, str]] | None:
        body = getattr(response, "body", None)
        if not isinstance(body, str):
            return None
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            return None
        if not isinstance(payload, dict) or "tools" not in payload:
            return None
        raw_tools = payload["tools"]
        if not isinstance(raw_tools, list):
            return None
        rows: list[tuple[str, str]] = []
        for item in raw_tools:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "")
            if not name:
                continue
            description = str(item.get("description") or "")
            rows.append((name, description))
        return rows

    def _drop_worker(self) -> None:
        worker = self._worker
        self._worker = None
        if worker is None:
            return
        try:
            worker.finished_ok.disconnect()
            worker.finished_error.disconnect()
        except (TypeError, RuntimeError):
            pass
        if worker.isRunning():
            worker.finished.connect(worker.deleteLater)
        else:
            worker.deleteLater()

    def _release_session(self) -> None:
        self._outbound_generation += 1
        self._list_in_flight = False
        self._progress_text = ""
        self._error_text = ""
        self._session = None
        self._state = McpClientSessionState.DISCONNECTED
        self._drop_worker()
        if self._tab is not None:
            self._tab.clear_tools()

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
        self._tab.set_session_state(
            self._state,
            list_in_flight=self._list_in_flight,
        )
        status = self._progress_text or self._error_text
        self._tab.set_status_text(status)
