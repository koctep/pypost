from __future__ import annotations

import logging
from typing import Callable, Protocol

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QPushButton,
    QWidget,
)

from pypost.core.config_manager import ConfigManager
from pypost.core.encryption_config import resolve_encryption_enabled
from pypost.core.env_variable_snapshot import EnvVariableSnapshot
from pypost.core.environment_import import load_import_candidates
from pypost.core.qt.environment_storage_gateway import EnvironmentStorageGateway
from pypost.core.mcp_tools_overview import collect_mcp_tool_overview
from pypost.core.mcp_activity_log import McpActivityEntry
from pypost.core.mcp_server_registry import MCPServerRegistry, McpServerStatus
from pypost.core.qt.mcp_server import MCPServerManager
from pypost.core.metrics_protocol import MetricsTrackerProtocol
from pypost.core.storage_interface import StorageInterface
from pypost.core.variable_name_validation import (
    validate_variable_name,
    validation_failure_reason,
)
from pypost.models.models import Environment
from pypost.models.settings import AppSettings, McpServerConfiguration
from pypost.ui.collection_item_dialogs import (
    show_env_save_failed,
    show_invalid_variable_name_error,
    show_mcp_server_start_failed,
    show_no_environment_selected,
)
from pypost.ui.dialogs.env_dialog import EnvironmentDialog
from pypost.ui.dialogs.mcp_activity_dialog import McpActivityDialog
from pypost.ui.dialogs.mcp_servers_dialog import McpServersDialog
from pypost.ui.dialogs.mcp_tools_overview_dialog import McpToolsOverviewDialog
from pypost.ui.widget_ids import (
    ENV_BAR,
    ENV_MANAGE_BUTTON,
    ENV_SELECTOR,
    set_widget_id,
)

logger = logging.getLogger(__name__)


class McpServerController(Protocol):
    """Persistence and lifecycle operations supplied by the owning window."""

    def mcp_server_configurations(self) -> list[McpServerConfiguration]: ...

    def mcp_server_status(self, instance_id: str) -> McpServerStatus: ...

    def upsert_mcp_server(self, configuration: McpServerConfiguration) -> None: ...

    def remove_mcp_server(self, instance_id: str) -> None: ...

    def start_mcp_server(self, instance_id: str) -> None: ...

    def stop_mcp_server(self, instance_id: str) -> None: ...

    def mcp_server_activity(self, instance_id: str) -> list[McpActivityEntry]: ...


class EnvPresenter(QObject):
    """Owns the environment selector: loading envs, propagating vars, managing MCP lifecycle."""

    env_variables_changed = Signal(object)  # payload: dict[str, str]
    env_keys_changed = Signal(object)  # payload: list[str] | None
    env_hidden_keys_changed = Signal(object)  # payload: set[str]
    environments_loaded = Signal()

    def __init__(
        self,
        storage: StorageInterface,
        config_manager: ConfigManager,
        mcp_manager: MCPServerManager,
        settings: AppSettings,
        get_collections: Callable,
        metrics: MetricsTrackerProtocol,
        mcp_registry: MCPServerRegistry | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._storage = storage
        self._config_manager = config_manager
        self._mcp_manager = mcp_manager
        # ``mcp_manager`` remains available for the legacy single-server
        # workflow and its focused tests.  A configured registry owns all
        # endpoint lifecycle instead, so an active editor environment can no
        # longer retarget a running MCP endpoint.
        self._mcp_registry = mcp_registry
        self._mcp_server_controller: McpServerController | None = None
        self._settings = settings
        self._get_collections = get_collections
        self._metrics = metrics
        self._environments: list[Environment] = []
        self._current_env_index: int = 0
        self._env_snapshot = EnvVariableSnapshot()
        self._pending_env_manager_refresh = False
        self._storage_gateway = EnvironmentStorageGateway(storage, parent=self)
        self._storage_gateway.load_completed.connect(self._on_storage_load_completed)
        self._storage_gateway.load_failed.connect(self._on_storage_load_failed)
        self._storage_gateway.save_failed.connect(self._on_storage_save_failed)

        self._mcp_manager.status_changed.connect(self._on_mcp_status_changed)
        self._mcp_manager.start_failed.connect(self._on_mcp_start_failed)
        self._mcp_manager.activity_recorded.connect(self._on_mcp_activity_recorded)
        self._mcp_manager.set_variable_supplier(self._env_snapshot.snapshot_variables)
        self._mcp_manager.set_hidden_keys_supplier(self._env_snapshot.snapshot_hidden_keys)

        # Build top-bar widget
        self._widget = QWidget()
        set_widget_id(self._widget, ENV_BAR)
        layout = QHBoxLayout(self._widget)
        layout.setContentsMargins(0, 0, 0, 0)

        self._env_label = QLabel("Environment:")
        self._env_selector = QComboBox()
        set_widget_id(self._env_selector, ENV_SELECTOR)
        self._env_selector.addItem("No Environment")
        self._env_selector.currentIndexChanged.connect(self._on_env_changed)

        self._manage_btn = QPushButton("Manage")
        set_widget_id(self._manage_btn, ENV_MANAGE_BUTTON)
        self._manage_btn.clicked.connect(self._open_env_manager)

        self._mcp_status_label = QLabel("MCP: OFF")
        self._mcp_status_label.setStyleSheet("color: gray;")

        self._mcp_tools_btn = QPushButton("MCP Tools (0)")
        self._mcp_tools_btn.clicked.connect(self._open_mcp_tools_overview)

        self._mcp_activity_btn = QPushButton("MCP Activity (0)")
        self._mcp_activity_btn.clicked.connect(self._open_mcp_activity)
        self._mcp_activity_dialog: McpActivityDialog | None = None

        self._mcp_servers_btn = QPushButton("MCP Servers…")
        self._mcp_servers_btn.clicked.connect(self._open_mcp_servers)

        if self._mcp_registry is not None:
            self._mcp_registry.status_changed.connect(
                self._on_mcp_registry_status_changed
            )

        layout.addWidget(self._env_label)
        layout.addWidget(self._env_selector)
        layout.addWidget(self._manage_btn)
        layout.addWidget(self._mcp_tools_btn)
        layout.addWidget(self._mcp_activity_btn)
        layout.addWidget(self._mcp_servers_btn)
        layout.addWidget(self._mcp_status_label)
        layout.addStretch()

        if self._mcp_registry is not None:
            self._refresh_mcp_registry_status_summary()

    @property
    def widget(self) -> QWidget:
        return self._widget

    @property
    def current_variables(self) -> dict[str, str]:
        """Returns currently active env vars."""
        selected = self._env_selector.currentData()
        if isinstance(selected, Environment):
            return dict(selected.variables)
        return {}

    @property
    def current_hidden_keys(self) -> set[str]:
        """Returns hidden keys for the currently active environment."""
        selected = self._env_selector.currentData()
        if isinstance(selected, Environment):
            return set(selected.hidden_keys)
        return set()

    def apply_settings(self, settings: AppSettings) -> None:
        self._settings = settings

    def set_mcp_server_controller(self, controller: McpServerController) -> None:
        """Attach MainWindow's persistence/lifecycle API to the server manager UI."""
        self._mcp_server_controller = controller

    def select_environment_index(self, index: int) -> None:
        """Select environment by combo index (0 = No Environment)."""
        self._env_selector.setCurrentIndex(index)

    def current_environment_index(self) -> int:
        return self._env_selector.currentIndex()

    def environment_count(self) -> int:
        return self._env_selector.count()

    def environment_display_name_at(self, index: int) -> str:
        return self._env_selector.itemText(index)

    def environment_at(self, index: int) -> Environment | None:
        data = self._env_selector.itemData(index)
        return data if isinstance(data, Environment) else None

    def environment_by_id(self, environment_id: str) -> Environment | None:
        """Resolve a persisted environment ID without consulting UI selection."""
        return next(
            (environment for environment in self._environments if environment.id == environment_id),
            None,
        )

    def mcp_status_text(self) -> str:
        return self._mcp_status_label.text()

    def mcp_tools_button_text(self) -> str:
        return self._mcp_tools_btn.text()

    def mcp_activity_button_text(self) -> str:
        return self._mcp_activity_btn.text()

    def reload_current_env(self) -> None:
        """Re-resolves variables and MCP state for the current combo selection."""
        self._on_env_changed(self._env_selector.currentIndex())

    def wait_storage_idle(self, timeout_ms: int = 30000) -> bool:
        return self._storage_gateway.wait_idle(timeout_ms)

    def load_environments(self) -> None:
        """Loads from storage, populates combo, emits current vars."""
        if self._encryption_enabled():
            logger.info("environment_storage_async_load_dispatched")
            self._storage_gateway.load_async()
            return
        environments = self._storage.load_environments()
        self._apply_loaded_environments(environments)
        self.environments_loaded.emit()

    def _encryption_enabled(self) -> bool:
        return resolve_encryption_enabled(self._settings)

    def _save_environments(self) -> None:
        if self._encryption_enabled():
            logger.info(
                "environment_storage_async_save_dispatched count=%d",
                len(self._environments),
            )
            self._storage_gateway.save_async(self._environments)
        else:
            self._storage.save_environments(self._environments)

    def _apply_loaded_environments(self, environments: list[Environment]) -> None:
        self._environments = environments
        logger.info("load_environments_completed count=%d", len(self._environments))

        self._env_selector.blockSignals(True)
        self._env_selector.clear()
        self._env_selector.addItem("No Environment", None)

        selected_index = 0
        for i, env in enumerate(self._environments):
            self._env_selector.addItem(env.name, env)
            if self._settings.last_environment_id == env.id:
                selected_index = i + 1

        self._env_selector.setCurrentIndex(selected_index)
        self._current_env_index = selected_index
        self._env_selector.blockSignals(False)

        if selected_index > 0:
            self._on_env_changed(selected_index)

    def _on_storage_load_completed(self, environments: list[Environment]) -> None:
        self._apply_loaded_environments(environments)
        if self._pending_env_manager_refresh:
            self._pending_env_manager_refresh = False
            self._on_env_changed(self._env_selector.currentIndex())
        self.environments_loaded.emit()

    def _on_storage_load_failed(self, error: object) -> None:
        logger.error("storage_load_failed error=%s", error)
        self._apply_loaded_environments([])
        self.environments_loaded.emit()

    def _on_storage_save_failed(self, error: object) -> None:
        message = str(error) if error else "Failed to save environments."
        logger.error("storage_save_failed error=%s", message)
        show_env_save_failed(self._widget, message)

    def on_env_update(self, vars: dict) -> None:
        """Merges post-request variable updates into current env."""
        selected = self._env_selector.currentData()
        if isinstance(selected, Environment):
            logger.info(
                "env_variables_updated_from_script env_id=%s env_name=%s var_count=%d",
                selected.id,
                selected.name,
                len(vars),
            )
            selected.variables.update(vars)
            self._save_environments()
            self._refresh_registry_environment(selected.id)
            self._on_env_changed(self._env_selector.currentIndex())

    def handle_variable_set_request(self, key, value: str) -> None:
        """Prompts for key if needed, saves variable to current env."""
        selected = self._env_selector.currentData()
        if not isinstance(selected, Environment):
            logger.warning("variable_set_request_no_env_selected")
            show_no_environment_selected(self._widget)
            return

        target_key = key
        if target_key is None:
            text, ok = QInputDialog.getText(self._widget, "New Variable", "Enter variable name:")
            if ok and text:
                target_key = text.strip()
                is_valid, error_msg = self._is_valid_variable_name(target_key)
                if not is_valid:
                    show_invalid_variable_name_error(self._widget, error_msg)
                    return
            else:
                return

        logger.info(
            "variable_set_in_env env_id=%s env_name=%s key=%s",
            selected.id,
            selected.name,
            target_key,
        )
        selected.variables[target_key] = value
        self._save_environments()
        self._refresh_registry_environment(selected.id)
        self._on_env_changed(self._env_selector.currentIndex())

    def _is_valid_variable_name(self, name: str) -> tuple[bool, str]:
        """Validate variable name and record metrics/logging for the UI flow."""
        is_valid, error_msg = validate_variable_name(name)
        if is_valid:
            self._metrics.track_variable_validation("valid")
            return True, ""

        reason = validation_failure_reason(name)
        if reason:
            self._metrics.track_variable_validation_failure(reason)
        self._metrics.track_variable_validation("invalid")
        logger.debug(
            "variable_name_validation_attempt name=%s valid=False error=%s",
            name,
            reason or "unknown",
        )
        return False, error_msg

    def handle_open_environments(self) -> None:
        """Shortcut handler — opens EnvironmentDialog."""
        self._open_env_manager()

    def _on_env_changed(self, index: int) -> None:
        """Resolves vars, starts/stops MCP, saves config, emits signals."""
        previous = self._env_selector.itemData(self._current_env_index)
        mcp_was_running = (
            self._mcp_manager.is_running() if self._mcp_registry is None else False
        )
        selected = self._env_selector.itemData(index)
        variables: dict = {}

        if isinstance(selected, Environment):
            logger.info(
                "env_selected env_id=%s env_name=%s mcp_enabled=%s var_count=%d",
                selected.id,
                selected.name,
                selected.enable_mcp,
                len(selected.variables),
            )
            self._settings.last_environment_id = selected.id
            variables = selected.variables

            if self._mcp_registry is None and selected.enable_mcp:
                tools = self._get_mcp_tools()
                self._mcp_manager.start_server(
                    port=self._settings.mcp_port,
                    tools=tools,
                    host=self._settings.mcp_host,
                )
                self._show_mcp_starting()
            elif self._mcp_registry is None:
                self._mcp_manager.stop_server()
        else:
            logger.info("env_deselected index=%d", index)
            self._settings.last_environment_id = None
            if self._mcp_registry is None:
                self._mcp_manager.stop_server()

        self._config_manager.save_config(self._settings)
        self._current_env_index = index
        hidden_keys = selected.hidden_keys if isinstance(selected, Environment) else set()
        self._env_snapshot.update(variables, hidden_keys)

        keys = list(variables.keys()) if isinstance(selected, Environment) else None
        self.env_variables_changed.emit(variables)
        self.env_keys_changed.emit(keys)
        self.env_hidden_keys_changed.emit(hidden_keys)
        self._refresh_mcp_tools_button()
        if mcp_was_running:
            self._track_mcp_active_env_changed(previous, selected)

    def _track_mcp_active_env_changed(
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

    def refresh_mcp_tools(self) -> None:
        """Refresh MCP tool list when collections change while server is running."""
        if self._mcp_registry is not None:
            self._mcp_registry.reconcile_references()
            for collection in self._get_collections():
                self._mcp_registry.refresh_collection(collection.id)
            self._refresh_mcp_tools_button()
            return
        tools = self._get_mcp_tools()
        self._refresh_mcp_tools_button()
        selected = self._env_selector.currentData()
        if not isinstance(selected, Environment) or not selected.enable_mcp:
            return
        if self._mcp_manager.update_tools(tools):
            self._show_mcp_starting()

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
        show_mcp_server_start_failed(self._widget, message)

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
        dialog = McpToolsOverviewDialog(entries, self._widget)
        dialog.exec()

    def _open_mcp_activity(self) -> None:
        entries = self._mcp_manager.activity_log.get_entries()
        logger.info("mcp_activity_dialog_opened entry_count=%d", len(entries))
        dialog = McpActivityDialog(entries, self._widget)
        self._mcp_activity_dialog = dialog
        dialog.finished.connect(self._on_mcp_activity_dialog_closed)
        dialog.exec()

    def _open_mcp_servers(self) -> None:
        """Open the explicit multi-server manager from the MCP portion of the bar."""
        controller = self._mcp_server_controller
        if controller is None:
            logger.warning("mcp_servers_dialog_no_controller")
            return
        dialog = McpServersDialog(
            configurations=controller.mcp_server_configurations,
            status_for=controller.mcp_server_status,
            save=controller.upsert_mcp_server,
            remove=controller.remove_mcp_server,
            start=controller.start_mcp_server,
            stop=controller.stop_mcp_server,
            activity=controller.mcp_server_activity,
            collections=self._get_collections,
            environments=lambda: list(self._environments),
            legacy_environment=self._selected_legacy_mcp_environment,
            legacy_host=self._settings.mcp_host,
            legacy_port=self._settings.mcp_port,
            parent=self._widget,
        )
        dialog.exec()

    def _selected_legacy_mcp_environment(self) -> Environment | None:
        selected = self._env_selector.currentData()
        if isinstance(selected, Environment) and selected.enable_mcp:
            return selected
        return None

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

    def _open_env_manager(self) -> None:
        current_env_name = self._env_selector.currentText()
        if self._env_selector.currentIndex() == 0:
            current_env_name = None

        logger.info("env_manager_dialog_opened current_env=%s", current_env_name)
        dialog = EnvironmentDialog(
            self._environments,
            self._widget,
            current_env_name,
            log_hidden_key_names=self._settings.log_hidden_key_names,
            read_import_file=lambda path: load_import_candidates(path, self._storage),
            serialize_export_records=self._storage.serialize_environment_records,
        )
        dialog.exec()
        logger.info("env_manager_dialog_closed")
        self._environments = dialog.environments
        self._save_environments()
        if self._mcp_registry is not None:
            self._mcp_registry.reconcile_references()
        for environment in self._environments:
            self._refresh_registry_environment(environment.id)
        if self._encryption_enabled():
            self._pending_env_manager_refresh = True
        self.load_environments()
        if not self._encryption_enabled():
            self._on_env_changed(self._env_selector.currentIndex())

    def _get_mcp_tools(self) -> list:
        """Returns expose_as_mcp requests from current collections."""
        tools = []
        for col in self._get_collections():
            for req in col.requests:
                if req.expose_as_mcp:
                    tools.append(req)
        return tools

    def _refresh_registry_environment(self, environment_id: str) -> None:
        """Update only endpoints explicitly configured for this environment."""
        if self._mcp_registry is not None:
            self._mcp_registry.refresh_environment(environment_id)
