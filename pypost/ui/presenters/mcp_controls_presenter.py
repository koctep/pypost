"""MCP status controls, dialog routing and refresh fan-out (PYPOST-1071).

Extracted from ``EnvPresenter``: PYPOST-1044 grew the environment presenter with
multi-server status rendering, per-endpoint dialogs and scoped registry refreshes, none of
which are environment state.
"""
from __future__ import annotations

import logging
from typing import Callable, Protocol

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QLabel, QPushButton, QWidget

from pypost.core.mcp_activity_log import McpActivityEntry
from pypost.core.mcp_server_registry import MCPServerRegistry, McpServerStatus
from pypost.core.mcp_tools_overview import collect_mcp_tool_overview
from pypost.core.metrics_protocol import MetricsTrackerProtocol
from pypost.core.qt.mcp_server import MCPServerManager
from pypost.models.models import Environment
from pypost.models.settings import AppSettings, McpServerConfiguration
from pypost.ui.collection_item_dialogs import show_mcp_server_start_failed
from pypost.ui.dialogs.mcp_activity_dialog import McpActivityDialog
from pypost.ui.dialogs.mcp_servers_dialog import McpServersDialog
from pypost.ui.dialogs.mcp_tools_overview_dialog import McpToolsOverviewDialog

logger = logging.getLogger(__name__)


class McpServerController(Protocol):
    """Persistence and lifecycle operations supplied by the owning window."""

    def mcp_server_configurations(self) -> list[McpServerConfiguration]: ...

    def mcp_server_count(self) -> int: ...

    def mcp_server_status(self, instance_id: str) -> McpServerStatus: ...

    def upsert_mcp_server(self, configuration: McpServerConfiguration) -> None: ...

    def save_library_server(self, configuration, selection, handoff) -> None: ...

    def remove_mcp_server(self, instance_id: str) -> None: ...

    def start_mcp_server(self, instance_id: str) -> None: ...

    def stop_mcp_server(self, instance_id: str) -> None: ...

    def mcp_server_activity(self, instance_id: str) -> list[McpActivityEntry]: ...


class McpControlsPresenter(QObject):
    """Owns the MCP portion of the environment bar: buttons, status, and dialogs."""

    def __init__(
        self,
        *,
        mcp_manager: MCPServerManager,
        settings_provider: Callable[[], AppSettings],
        get_collections: Callable[[], list],
        get_environments: Callable[[], list[Environment]],
        current_environment: Callable[[], Environment | None],
        metrics: MetricsTrackerProtocol,
        dialog_parent: QWidget,
        mcp_registry: MCPServerRegistry | None = None,
        library_service=None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._mcp_manager = mcp_manager
        self._settings_provider = settings_provider
        self._get_collections = get_collections
        self._get_environments = get_environments
        self._current_environment = current_environment
        self._metrics = metrics
        self._dialog_parent = dialog_parent
        # ``mcp_manager`` remains available for the legacy single-server workflow and its
        # focused tests.  A configured registry owns all endpoint lifecycle instead, so an
        # active editor environment can no longer retarget a running MCP endpoint.
        self._mcp_registry = mcp_registry
        self._library_service = library_service
        self._mcp_server_controller: McpServerController | None = None
        self._active_environment: Environment | None = None

        self._mcp_status_label = QLabel("MCP: OFF")
        self._mcp_status_label.setStyleSheet("color: gray;")

        self._mcp_tools_btn = QPushButton("MCP Tools (0)")
        self._mcp_tools_btn.clicked.connect(self._open_mcp_tools_overview)

        self._mcp_activity_btn = QPushButton("MCP Activity (0)")
        self._mcp_activity_btn.clicked.connect(self._open_mcp_activity)
        self._mcp_activity_dialog: McpActivityDialog | None = None

        self._mcp_servers_btn = QPushButton("MCP Servers…")
        self._mcp_servers_btn.clicked.connect(self._open_mcp_servers)

        self._mcp_manager.status_changed.connect(self._on_mcp_status_changed)
        self._mcp_manager.start_failed.connect(self._on_mcp_start_failed)
        self._mcp_manager.activity_recorded.connect(self._on_mcp_activity_recorded)

        if self._mcp_registry is not None:
            self._mcp_registry.status_changed.connect(
                self._on_mcp_registry_status_changed
            )
            self._refresh_mcp_registry_status_summary()

    @property
    def _settings(self) -> AppSettings:
        return self._settings_provider()

    @property
    def widgets(self) -> tuple[QWidget, ...]:
        """Bar widgets in display order, inserted by the owning environment presenter."""
        return (
            self._mcp_tools_btn,
            self._mcp_activity_btn,
            self._mcp_servers_btn,
            self._mcp_status_label,
        )

    # -- read-only text surface, mirrored by EnvPresenter's public shims ----------------

    def status_text(self) -> str:
        return self._mcp_status_label.text()

    def tools_button_text(self) -> str:
        return self._mcp_tools_btn.text()

    def activity_button_text(self) -> str:
        return self._mcp_activity_btn.text()

    # -- collaboration with the environment presenter ----------------------------------

    def set_server_controller(self, controller: McpServerController) -> None:
        """Attach the window's persistence/lifecycle API to the server manager UI."""
        self._mcp_server_controller = controller
        if self._library_service is None:
            registry = getattr(controller, "registry", None)
            self._library_service = getattr(registry, "library_service", None)

    def legacy_server_running(self) -> bool:
        """True only while the single-server workflow owns a running endpoint."""
        return self._mcp_manager.is_running() if self._mcp_registry is None else False

    def handle_environment_selected(self, selected: object) -> None:
        """Apply the legacy single-server start/stop rule for the new selection."""
        selected_env = selected if isinstance(selected, Environment) else None
        mcp_was_running = self.legacy_server_running()
        previous = self._active_environment
        logger.debug(
            "mcp_handle_environment_selected env_id=%s mcp_enabled=%s legacy_running=%s",
            selected_env.id if selected_env else None,
            selected_env.enable_mcp if selected_env else False,
            mcp_was_running,
        )
        if self._mcp_registry is not None:
            self._active_environment = selected_env
            self._refresh_mcp_tools_button()
            if mcp_was_running:
                self.track_active_env_changed(previous, selected_env)
            return
        if selected_env is not None and selected_env.enable_mcp:
            self._mcp_manager.start_server(
                port=self._settings.mcp_port,
                tools=self._get_mcp_tools(),
                host=self._settings.mcp_host,
            )
            self._show_mcp_starting()
        else:
            self._mcp_manager.stop_server()
        self._active_environment = selected_env
        self._refresh_mcp_tools_button()
        if mcp_was_running:
            self.track_active_env_changed(previous, selected_env)

    def on_environment_manager_closed(self) -> None:
        """Reconcile references and refresh configurations after environment manager closes."""
        logger.debug("mcp_on_environment_manager_closed")
        self.reconcile_references()
        for environment in self._get_environments():
            self.refresh_environment(environment.id)
        self._refresh_mcp_tools_button()

    def track_active_env_changed(
        self,
        previous: Environment | None,
        selected: Environment | None,
    ) -> None:
        prev_id = previous.id if isinstance(previous, Environment) else None
        new_id = selected.id if isinstance(selected, Environment) else None
        if prev_id == new_id:
            return
        self._metrics.track_mcp_active_env_changed()
        logger.info(
            "mcp_active_env_changed prev_env_id=%s new_env_id=%s",
            prev_id or "",
            new_id or "",
        )

    def refresh_tools(self) -> None:
        """Refresh MCP tool list when collections change while server is running."""
        if self._mcp_registry is not None:
            self._mcp_registry.reconcile_references()
            for collection in self._get_collections():
                self._mcp_registry.refresh_collection(collection.id)
            self._refresh_mcp_tools_button()
            return
        tools = self._get_mcp_tools()
        self._refresh_mcp_tools_button()
        selected = self._current_environment()
        if selected is None or not selected.enable_mcp:
            return
        if self._mcp_manager.update_tools(tools):
            self._show_mcp_starting()

    def refresh_tools_button(self) -> None:
        self._refresh_mcp_tools_button()

    def reconcile_references(self) -> None:
        """Drop registry references to collections/environments that no longer exist."""
        logger.debug("mcp_reconcile_references")
        if self._mcp_registry is not None:
            self._mcp_registry.reconcile_references()

    def refresh_environment(self, environment_id: str) -> None:
        """Update only endpoints explicitly configured for this environment."""
        logger.debug("mcp_refresh_environment env_id=%s", environment_id)
        if self._mcp_registry is not None:
            self._mcp_registry.refresh_environment(environment_id)

    # -- internals ---------------------------------------------------------------------

    def _get_mcp_tools(self) -> list:
        """Returns expose_as_mcp requests from current collections."""
        tools = []
        for col in self._get_collections():
            for req in col.requests:
                if req.expose_as_mcp:
                    tools.append(req)
        return tools

    def _refresh_mcp_tools_button(self) -> None:
        if self._mcp_registry is not None:
            # An aggregate list is misleading once endpoints select different
            # collections. The manager routes the user to a row-specific view.
            self._mcp_tools_btn.setText("MCP Server Tools…")
            self._mcp_tools_btn.setToolTip(
                "Open MCP Servers and select a server to view its tools."
            )
            return
        count = len(self._get_mcp_tools())
        self._mcp_tools_btn.setText(f"MCP Tools ({count})")

    def _show_mcp_starting(self) -> None:
        self._mcp_status_label.setText(
            f"MCP: Starting ({self._settings.mcp_host}:{self._settings.mcp_port})..."
        )
        self._mcp_status_label.setStyleSheet("color: #b8860b; font-weight: bold;")

    def _on_mcp_status_changed(self, is_running: bool) -> None:
        if is_running:
            logger.info(
                "mcp_server_started host=%s port=%d",
                self._settings.mcp_host,
                self._settings.mcp_port,
            )
            self._mcp_status_label.setText(
                f"MCP: ON ({self._settings.mcp_host}:{self._settings.mcp_port})"
            )
            self._mcp_status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            logger.info("mcp_server_stopped")
            self._mcp_status_label.setText("MCP: OFF")
            self._mcp_status_label.setStyleSheet("color: gray;")

    def _on_mcp_start_failed(self, message: str) -> None:
        logger.error("mcp_server_start_failed_ui message=%s", message)
        self._mcp_status_label.setText("MCP: OFF")
        self._mcp_status_label.setStyleSheet("color: gray;")
        show_mcp_server_start_failed(self._dialog_parent, message)

    def _on_mcp_registry_status_changed(
        self, _instance_id: str, _state: str, _message: str
    ) -> None:
        """Render aggregate multi-server state without exposing endpoint details."""
        self._refresh_mcp_registry_status_summary()

    def _refresh_mcp_registry_status_summary(self) -> None:
        """Show a concise, non-sensitive summary for independently managed servers."""
        if self._mcp_registry is None:
            return
        statuses = self._mcp_registry.list_statuses()
        running = sum(status.state == "running" for status in statuses)
        failed = sum(status.state == "failed" for status in statuses)
        suffix = f"; {failed} failed" if failed else ""
        self._mcp_status_label.setText(f"MCP Servers: {running} running{suffix}")
        color = "#b00020" if failed else ("green" if running else "gray")
        self._mcp_status_label.setStyleSheet(f"color: {color};")

    def _open_mcp_tools_overview(self) -> None:
        if self._mcp_registry is not None:
            self._open_mcp_servers()
            return
        entries = collect_mcp_tool_overview(self._get_collections())
        logger.info("mcp_tools_overview_opened tool_count=%d", len(entries))
        dialog = McpToolsOverviewDialog(entries, self._dialog_parent)
        dialog.exec()

    def _open_mcp_activity(self) -> None:
        entries = self._mcp_manager.activity_log.get_entries()
        logger.info("mcp_activity_dialog_opened entry_count=%d", len(entries))
        dialog = McpActivityDialog(entries, self._dialog_parent)
        self._mcp_activity_dialog = dialog
        dialog.finished.connect(self._on_mcp_activity_dialog_closed)
        dialog.exec()

    def _open_mcp_servers(self) -> None:
        """Open the explicit multi-server manager from the MCP portion of the bar."""
        controller = self._mcp_server_controller
        if controller is None:
            logger.warning("mcp_servers_dialog_no_controller")
            return
        settings = self._settings
        # The sibling dialogs already log their open with a count; this one is also the
        # single entry point for every `mcp_servers_persist_requested` mutation below it.
        logger.info(
            "mcp_servers_dialog_opened server_count=%d",
            controller.mcp_server_count(),
        )
        dialog = McpServersDialog(
            configurations=controller.mcp_server_configurations,
            status_for=controller.mcp_server_status,
            save=controller.upsert_mcp_server,
            save_library=getattr(controller, "save_library_server", None),
            remove=controller.remove_mcp_server,
            start=controller.start_mcp_server,
            stop=controller.stop_mcp_server,
            activity=controller.mcp_server_activity,
            collections=self._get_collections,
            environments=lambda: list(self._get_environments()),
            legacy_environment=self._selected_legacy_mcp_environment,
            legacy_host=settings.mcp_host,
            legacy_port=settings.mcp_port,
            library_service=self._library_service,
            parent=self._dialog_parent,
        )
        dialog.exec()

    def _selected_legacy_mcp_environment(self) -> Environment | None:
        selected = (
            self._active_environment
            if self._active_environment is not None
            else self._current_environment()
        )
        return selected if selected is not None and selected.enable_mcp else None

    def _on_mcp_activity_dialog_closed(self) -> None:
        self._mcp_activity_dialog = None

    def _on_mcp_activity_recorded(self, _entry: object) -> None:
        self._refresh_mcp_activity_button()
        if self._mcp_activity_dialog is not None:
            self._mcp_activity_dialog.set_entries(
                self._mcp_manager.activity_log.get_entries()
            )

    def _refresh_mcp_activity_button(self) -> None:
        count = self._mcp_manager.activity_log.count()
        self._mcp_activity_btn.setText(f"MCP Activity ({count})")
