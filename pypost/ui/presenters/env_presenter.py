from __future__ import annotations
import logging
import threading
from typing import Callable

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
from pypost.core.environment_variable_resolver import resolve_environment_variables
from pypost.core.environment_variable_validation import (
    EnvironmentVariableValidationError,
    apply_environment_variable_updates,
)
from pypost.core.qt.environment_storage_gateway import EnvironmentStorageGateway
from pypost.core.lifecycle import TeardownResult
from pypost.core.qt.mcp_server import MCPServerManager
from pypost.core.qt.mcp_server_registry import QtMCPServerRegistry
from pypost.core.qt.state_manager import StateManager
from pypost.core.metrics_protocol import MetricsTrackerProtocol
from pypost.core.storage_interface import StorageInterface
from pypost.models.models import Environment
from pypost.models.settings import AppSettings
from pypost.ui.collection_item_dialogs import (
    show_env_save_failed,
    show_invalid_variable_name_error,
    show_no_environment_selected,
)
from pypost.ui.dialogs.env_dialog import EnvironmentDialog
from pypost.ui.presenters.mcp_controls_presenter import McpControlsPresenter
from pypost.ui.presenters import env_presenter_lifecycle
from pypost.ui.presenters import env_presenter_dialog
from pypost.ui.widget_ids import (
    ENV_BAR,
    ENV_MANAGE_BUTTON,
    ENV_SELECTOR,
    set_widget_id,
)

logger = logging.getLogger(__name__)


class EnvPresenter(QObject):
    """Owns the environment selector: loading envs, propagating vars, and environment selection."""

    env_variables_changed = Signal(dict)  # payload: dict[str, str]
    env_keys_changed = Signal(object)  # payload: list[str] | None
    env_hidden_keys_changed = Signal(set)  # payload: set[str]
    environments_loaded = Signal()
    environment_selected = Signal(object)  # payload: Environment | None
    environment_updated = Signal(str)  # payload: environment_id
    environment_update_disposition = Signal(int, str)
    environment_manager_closed = Signal()  # payload: None

    def __init__(
        self,
        storage: StorageInterface,
        config_manager: ConfigManager,
        mcp_manager: MCPServerManager,
        settings: AppSettings,
        get_collections: Callable,
        metrics: MetricsTrackerProtocol,
        mcp_registry: QtMCPServerRegistry | None = None,
        state_manager: StateManager | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._storage = storage
        self._config_manager = config_manager
        self._mcp_manager = mcp_manager
        self._settings = settings
        self._state_manager = state_manager
        self._get_collections = get_collections
        self._metrics = metrics
        self._environments: list[Environment] = []
        self._current_env_index: int = 0
        self._env_snapshot = EnvVariableSnapshot()
        self._pending_env_manager_refresh = False
        self._lifecycle_lock = threading.RLock()
        self._teardown_lock = threading.Lock()
        self._root_teardown_started = False
        self._teardown_started = False
        self._teardown_result: TeardownResult | None = None
        self._storage_gateway = EnvironmentStorageGateway(storage, parent=self, metrics=metrics)
        self._storage_gateway.load_completed.connect(self._on_storage_load_completed)
        self._storage_gateway.load_failed.connect(self._on_storage_load_failed)
        self._storage_gateway.save_failed.connect(self._on_storage_save_failed)
        self._storage_gateway.save_outcome.connect(
            lambda sequence, outcome: self._on_storage_save_outcome(sequence, outcome)
        )

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

        self._mcp_controls = McpControlsPresenter(
            mcp_manager=mcp_manager,
            settings_provider=lambda: self._settings,
            get_collections=get_collections,
            get_environments=lambda: self._environments,
            current_environment=self._selected_environment,
            metrics=metrics,
            dialog_parent=self._widget,
            mcp_registry=mcp_registry,
            parent=self,
        )

        layout.addWidget(self._env_label)
        layout.addWidget(self._env_selector)
        layout.addWidget(self._manage_btn)
        for mcp_widget in self._mcp_controls.widgets:
            layout.addWidget(mcp_widget)
        layout.addStretch()

    @property
    def widget(self) -> QWidget:
        return self._widget

    @property
    def current_variables(self) -> dict[str, str]:
        """Returns currently active env vars."""
        selected = self._env_selector.currentData()
        if isinstance(selected, Environment):
            return resolve_environment_variables(selected.variables)
        return {}

    @property
    def current_hidden_keys(self) -> set[str]:
        """Returns hidden keys for the currently active environment."""
        selected = self._env_selector.currentData()
        if isinstance(selected, Environment):
            return set(selected.hidden_keys)
        return set()

    def apply_settings(self, settings: AppSettings) -> None:
        if self._admission_closed():
            return
        self._settings = settings

    def _selected_environment(self) -> Environment | None:
        selected = self._env_selector.currentData()
        return selected if isinstance(selected, Environment) else None

    def select_environment_index(self, index: int) -> None:
        """Select environment by combo index (0 = No Environment)."""
        if self._admission_closed():
            return
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

    @property
    def mcp_controls(self) -> McpControlsPresenter:
        return self._mcp_controls

    def reload_current_env(self) -> None:
        """Re-resolves variables and MCP state for the current combo selection."""
        self._on_env_changed(self._env_selector.currentIndex())

    def wait_storage_idle(self, timeout_ms: int = 30000) -> bool:
        return self._storage_gateway.wait_idle(timeout_ms)

    def begin_root_teardown(self) -> None:
        """Close UI admission while accepted request updates are still drained."""
        with self._lifecycle_lock:
            self._root_teardown_started = True

    def _admission_closed(self) -> bool:
        return self._root_teardown_started or self._teardown_started

    def teardown(self, timeout_ms: int | None = None) -> TeardownResult:
        return env_presenter_lifecycle.teardown(self, timeout_ms)

    def begin_teardown(self) -> None:
        env_presenter_lifecycle.begin_teardown(self)

    def load_environments(self) -> None:
        """Loads from storage, populates combo, emits current vars."""
        with self._lifecycle_lock:
            if self._admission_closed():
                logger.info("environment_load_rejected reason=teardown")
                return
            if self._encryption_enabled():
                logger.info("environment_storage_async_load_dispatched")
                self._storage_gateway.load_async()
                return
            environments = self._storage.load_environments()
            self._apply_loaded_environments(environments)
            self.environments_loaded.emit()

    def _encryption_enabled(self) -> bool:
        return resolve_encryption_enabled(self._settings)

    def _save_environments(
        self,
        *,
        update_sequences: tuple[int, ...] = (),
        accepted_during_teardown: bool = False,
    ) -> bool:
        with self._lifecycle_lock:
            if self._admission_closed() and not accepted_during_teardown:
                logger.info("environment_save_rejected reason=teardown")
                return False
            if self._encryption_enabled():
                logger.info(
                    "environment_storage_async_save_dispatched count=%d",
                    len(self._environments),
                )
                self._storage_gateway.save_async(
                    self._environments,
                    update_sequences=update_sequences,
                    accepted_during_teardown=accepted_during_teardown,
                )
                return True
            try:
                self._storage.save_environments(self._environments)
            except Exception:
                for sequence in update_sequences:
                    self.environment_update_disposition.emit(sequence, "failed")
                raise
            for sequence in update_sequences:
                self.environment_update_disposition.emit(sequence, "persisted")
            return True

    def _apply_loaded_environments(self, environments: list[Environment]) -> None:
        env_presenter_lifecycle.apply_loaded_environments(self, environments)

    def _on_storage_load_completed(self, environments: list[Environment]) -> None:
        env_presenter_lifecycle.on_storage_load_completed(self, environments)

    def _on_storage_save_outcome(self, sequence: object, outcome: str) -> None:
        env_presenter_lifecycle.on_storage_save_outcome(self, sequence, outcome)

    def _on_storage_load_failed(self, error: object) -> None:
        env_presenter_lifecycle.on_storage_load_failed(self, error)

    def _on_storage_save_failed(self, error: object) -> None:
        env_presenter_lifecycle.on_storage_save_failed(self, error, show_env_save_failed)

    def on_env_update(
        self,
        vars: dict,
        sequence: int | None = None,
        *,
        accepted_during_teardown: bool = False,
    ) -> None:
        """Merges post-request variable updates into current env."""
        with self._lifecycle_lock:
            if self._admission_closed() and not accepted_during_teardown:
                logger.info("environment_update_rejected reason=teardown")
                if sequence is not None:
                    self.environment_update_disposition.emit(
                        sequence, "rejected_after_cutoff"
                    )
                return
            selected = self._env_selector.currentData()
            if isinstance(selected, Environment):
                logger.info(
                    "env_variables_updated_from_script env_id=%s env_name=%s var_count=%d",
                    selected.id,
                    selected.name,
                    len(vars),
                )
                try:
                    apply_environment_variable_updates(selected, vars)
                except EnvironmentVariableValidationError as exc:
                    logger.warning(
                        "environment_update_rejected reason=%s",
                        exc.validation.failure.value if exc.validation.failure else "unknown",
                    )
                    if sequence is not None:
                        self.environment_update_disposition.emit(sequence, "failed")
                    return
                if not self._save_environments(
                    update_sequences=() if sequence is None else (sequence,),
                    accepted_during_teardown=accepted_during_teardown,
                ):
                    return
                if accepted_during_teardown:
                    return
                logger.debug("environment_updated_emitted env_id=%s source=script", selected.id)
                self.environment_updated.emit(selected.id)
                self._on_env_changed(self._env_selector.currentIndex())
            elif sequence is not None:
                self.environment_update_disposition.emit(sequence, "failed")

    def accept_accepted_env_update(self, variables: dict, sequence: int) -> None:
        """Persist a request update accepted before the root shutdown cutoff."""
        self.on_env_update(
            variables,
            sequence,
            accepted_during_teardown=True,
        )

    def handle_variable_set_request(self, key, value: str) -> None:
        """Prompts for key if needed, saves variable to current env."""
        if self._admission_closed():
            return
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

        if self._admission_closed():
            return

        try:
            apply_environment_variable_updates(selected, {target_key: value})
        except EnvironmentVariableValidationError as exc:
            show_invalid_variable_name_error(self._widget, str(exc))
            return

        logger.info(
            "variable_set_in_env env_id=%s env_name=%s key=%s",
            selected.id,
            selected.name,
            target_key,
        )
        self._save_environments()
        logger.debug("environment_updated_emitted env_id=%s source=manual_set", selected.id)
        self.environment_updated.emit(selected.id)
        self._on_env_changed(self._env_selector.currentIndex())

    def _is_valid_variable_name(self, name: str) -> tuple[bool, str]:
        return env_presenter_lifecycle.validate_variable(self, name)

    def handle_open_environments(self) -> None:
        """Shortcut handler — opens EnvironmentDialog."""
        self._open_env_manager()

    def _on_env_changed(self, index: int) -> None:
        """Resolves vars, saves config, and emits domain and variable signals."""
        if self._admission_closed():
            logger.info("environment_selection_ignored reason=teardown")
            return
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
            selected_environment_id = selected.id
            variables = resolve_environment_variables(selected.variables)
            selected_env: Environment | None = selected
        else:
            logger.info("env_deselected index=%d", index)
            selected_environment_id = None
            selected_env = None

        if self._state_manager is not None:
            self._state_manager.set_last_environment_id(selected_environment_id)
        else:
            # Compatibility seam for isolated presenter tests and embedders.
            self._settings.last_environment_id = selected_environment_id
            self._config_manager.save_config(self._settings)
        self._current_env_index = index
        hidden_keys = selected.hidden_keys if isinstance(selected, Environment) else set()
        self._env_snapshot.update(variables, hidden_keys)

        keys = list(variables.keys()) if isinstance(selected, Environment) else None
        self.env_variables_changed.emit(variables)
        self.env_keys_changed.emit(keys)
        self.env_hidden_keys_changed.emit(hidden_keys)
        logger.debug(
            "environment_selected_emitted env_id=%s",
            selected_env.id if selected_env else None,
        )
        self.environment_selected.emit(selected_env)

    def _open_env_manager(self) -> None:
        env_presenter_dialog.open_environment_manager(self, EnvironmentDialog)
