import logging
from typing import Callable

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QComboBox, QLabel, QPushButton,
    QInputDialog, QMessageBox,
)
from PySide6.QtCore import QObject, Signal

from pypost.core.storage import StorageManager
from pypost.core.config_manager import ConfigManager
from pypost.core.mcp_server import MCPServerManager
from pypost.models.models import Environment
from pypost.models.settings import AppSettings
from pypost.ui.dialogs.env_dialog import EnvironmentDialog

logger = logging.getLogger(__name__)


class EnvPresenter(QObject):
    """Owns the environment selector: loading envs, propagating vars, managing MCP lifecycle."""

    env_variables_changed = Signal(object)   # payload: dict[str, str]
    env_keys_changed = Signal(object)        # payload: list[str] | None

    def __init__(
        self,
        storage: StorageManager,
        config_manager: ConfigManager,
        mcp_manager: MCPServerManager,
        settings: AppSettings,
        get_collections: Callable,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._storage = storage
        self._config_manager = config_manager
        self._mcp_manager = mcp_manager
        self._settings = settings
        self._get_collections = get_collections
        self._environments: list[Environment] = []
        self._current_env_index: int = 0

        self._mcp_manager.status_changed.connect(self._on_mcp_status_changed)

        # Build top-bar widget
        self._widget = QWidget()
        layout = QHBoxLayout(self._widget)
        layout.setContentsMargins(0, 0, 0, 0)

        self._env_label = QLabel("Environment:")
        self._env_selector = QComboBox()
        self._env_selector.addItem("No Environment")
        self._env_selector.currentIndexChanged.connect(self._on_env_changed)

        self._manage_btn = QPushButton("Manage")
        self._manage_btn.clicked.connect(self._open_env_manager)

        self._mcp_status_label = QLabel("MCP: OFF")
        self._mcp_status_label.setStyleSheet("color: gray;")

        layout.addWidget(self._env_label)
        layout.addWidget(self._env_selector)
        layout.addWidget(self._manage_btn)
        layout.addWidget(self._mcp_status_label)
        layout.addStretch()

    @property
    def widget(self) -> QWidget:
        return self._widget

    @property
    def current_variables(self) -> dict:
        """Returns currently active env vars."""
        selected = self._env_selector.currentData()
        if isinstance(selected, Environment):
            return dict(selected.variables)
        return {}

    @property
    def env_selector(self) -> QComboBox:
        """Exposes the combo box for MainWindow layout integration."""
        return self._env_selector

    @property
    def manage_btn(self) -> QPushButton:
        return self._manage_btn

    @property
    def mcp_status_label(self) -> QLabel:
        return self._mcp_status_label

    @property
    def env_label(self) -> QLabel:
        return self._env_label

    def load_environments(self) -> None:
        """Loads from storage, populates combo, emits current vars."""
        self._environments = self._storage.load_environments()
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

    def on_env_update(self, vars: dict) -> None:
        """Merges post-request variable updates into current env."""
        selected = self._env_selector.currentData()
        if isinstance(selected, Environment):
            logger.info(
                "env_variables_updated_from_script env_id=%s env_name=%s var_count=%d",
                selected.id, selected.name, len(vars),
            )
            selected.variables.update(vars)
            self._storage.save_environments(self._environments)
            self._on_env_changed(self._env_selector.currentIndex())

    def handle_variable_set_request(self, key, value: str) -> None:
        """Prompts for key if needed, saves variable to current env."""
        selected = self._env_selector.currentData()
        if not isinstance(selected, Environment):
            logger.warning("variable_set_request_no_env_selected")
            QMessageBox.warning(
                self._widget, "No Environment",
                "Please select an environment to set variables.",
            )
            return

        target_key = key
        if target_key is None:
            text, ok = QInputDialog.getText(self._widget, "New Variable", "Enter variable name:")
            if ok and text:
                target_key = text.strip()
                if not target_key:
                    QMessageBox.warning(
                        self._widget, "Invalid Name", "Variable name cannot be empty."
                    )
                    return
            else:
                return

        logger.info(
            "variable_set_in_env env_id=%s env_name=%s key=%s",
            selected.id, selected.name, target_key,
        )
        selected.variables[target_key] = value
        self._storage.save_environments(self._environments)
        self._on_env_changed(self._env_selector.currentIndex())

    def handle_open_environments(self) -> None:
        """Shortcut handler — opens EnvironmentDialog."""
        self._open_env_manager()

    def _on_env_changed(self, index: int) -> None:
        """Resolves vars, starts/stops MCP, saves config, emits signals."""
        selected = self._env_selector.itemData(index)
        variables: dict = {}

        if isinstance(selected, Environment):
            logger.info(
                "env_selected env_id=%s env_name=%s mcp_enabled=%s var_count=%d",
                selected.id, selected.name, selected.enable_mcp, len(selected.variables),
            )
            self._settings.last_environment_id = selected.id
            variables = selected.variables

            if selected.enable_mcp:
                tools = self._get_mcp_tools()
                self._mcp_manager.start_server(
                    port=self._settings.mcp_port,
                    tools=tools,
                    host=self._settings.mcp_host,
                )
            else:
                self._mcp_manager.stop_server()
        else:
            logger.info("env_deselected index=%d", index)
            self._settings.last_environment_id = None
            self._mcp_manager.stop_server()

        self._config_manager.save_config(self._settings)
        self._current_env_index = index

        keys = list(variables.keys()) if isinstance(selected, Environment) else None
        self.env_variables_changed.emit(variables)
        self.env_keys_changed.emit(keys)

    def _on_mcp_status_changed(self, is_running: bool) -> None:
        if is_running:
            logger.info(
                "mcp_server_started host=%s port=%d",
                self._settings.mcp_host, self._settings.mcp_port,
            )
            self._mcp_status_label.setText(
                f"MCP: ON ({self._settings.mcp_host}:{self._settings.mcp_port})"
            )
            self._mcp_status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            logger.info("mcp_server_stopped")
            self._mcp_status_label.setText("MCP: OFF")
            self._mcp_status_label.setStyleSheet("color: gray;")

    def _open_env_manager(self) -> None:
        current_env_name = self._env_selector.currentText()
        if self._env_selector.currentIndex() == 0:
            current_env_name = None

        logger.info("env_manager_dialog_opened current_env=%s", current_env_name)
        dialog = EnvironmentDialog(self._environments, self._widget, current_env_name)
        dialog.exec()
        logger.info("env_manager_dialog_closed")
        self._storage.save_environments(self._environments)
        self.load_environments()
        self._on_env_changed(self._env_selector.currentIndex())

    def _get_mcp_tools(self) -> list:
        """Returns expose_as_mcp requests from current collections."""
        tools = []
        for col in self._get_collections():
            for req in col.requests:
                if req.expose_as_mcp:
                    tools.append(req)
        return tools
