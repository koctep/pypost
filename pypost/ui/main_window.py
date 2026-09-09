from __future__ import annotations

import logging
import threading
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from pypost.core.alert_manager import AlertManager
from pypost.core.config_manager import ConfigManager, ConfigRecoveryNotice
from pypost.core.encryption_config import resolve_encryption_enabled
from pypost.core.history_manager import HistoryManager
from pypost.core.lifecycle import TeardownResult
from pypost.core.mcp_server_registry import MCPServerRegistry
from pypost.core.qt.mcp_server import MCPServerManager
from pypost.core.qt.metrics import MetricsManager
from pypost.core.request_manager import RequestManager
from pypost.core.qt.state_manager import StateManager
from pypost.core.storage import StorageManager
from pypost.ui.styles.style_manager import StyleManager
from pypost.core.template_service import TemplateService
from pypost.models.settings import AppSettings
from pypost.ui.collection_item_dialogs import show_metrics_server_start_failed
from pypost.ui.hotkeys import register_hotkey, register_hotkey_group, tag_action
from pypost.ui.main_window_protocol_hotkeys import register_protocol_session_hotkeys
from pypost.ui import main_window_lifecycle
from pypost.ui import main_window_settings
from pypost.ui.dialogs.settings_dialog import SettingsDialog
from pypost.ui.main_window_signals import wire_presenter_signals
from pypost.ui.mcp_server_controller import McpServerSettingsController
from pypost.ui.presenters import CollectionsPresenter, EnvPresenter, TabsPresenter
from pypost.ui.widget_ids import LIBRARY_MANAGER_BUTTON, MAIN_WINDOW, SETTINGS_BUTTON, set_widget_id
from pypost.ui.widgets.history_panel import HistoryPanel
from pypost.ui.widgets.mixins import VariableHoverResolver

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(
        self,
        metrics: MetricsManager,
        template_service: TemplateService,
        *,
        config_manager: ConfigManager,
        settings: AppSettings,
        state_manager: StateManager,
        alert_manager: AlertManager | None = None,
        history_manager: HistoryManager | None = None,
        storage: StorageManager | None = None,
        request_manager: RequestManager | None = None,
        mcp_manager: MCPServerManager | None = None,
        mcp_registry: MCPServerRegistry | None = None,
        defer_startup: bool = False,
        alert_log_path_override: Path | None = None,
        default_alert_log_path: Path | None = None,
    ) -> None:
        super().__init__()
        set_widget_id(self, MAIN_WINDOW)
        self.setWindowTitle("PyPost")
        self.resize(1200, 800)
        self.metrics = metrics
        self.metrics.connect_start_failed(self._on_metrics_start_failed)
        self.template_service = template_service
        VariableHoverResolver.set_template_service(template_service)
        if storage is not None:
            logger.debug("storage_source source=injected")
            self.storage = storage
        else:
            logger.debug("storage_source source=new")
            self.storage = StorageManager(metrics=self.metrics)
        self.config_manager = config_manager
        self._alert_manager = alert_manager
        self._alert_log_path_override = alert_log_path_override
        self._default_alert_log_path = default_alert_log_path
        logger.debug("MainWindow: alert_manager_injected=%s", alert_manager is not None)
        if request_manager is not None:
            logger.debug("request_manager_source source=injected")
            self.request_manager = request_manager
        else:
            logger.debug("request_manager_source source=new")
            self.request_manager = RequestManager(self.storage, defer_initial_load=True)
        if state_manager.settings is not settings:
            raise ValueError("MainWindow and StateManager must share one AppSettings instance")
        self.state_manager = state_manager
        self.state_manager.setParent(self)
        self.state_manager.persistence_failed.connect(self._on_settings_persistence_failed)
        if storage is None:
            self.storage.apply_encryption_settings(settings)
        self.style_manager = StyleManager()
        self._settings = settings
        self._teardown_lock = threading.Lock()
        self._teardown_started = False
        self._teardown_result: TeardownResult | None = None
        self.icons = self._load_icons()
        if history_manager is not None:
            logger.debug("history_manager_source source=injected")
            self.history_manager = history_manager
        else:
            logger.debug("history_manager_source source=new")
            self.history_manager = HistoryManager(defer_initial_load=True, metrics=self.metrics)
        self.collections = CollectionsPresenter(
            self.request_manager,
            self.state_manager,
            self.metrics,
            self.icons,
            storage=self.storage,
        )
        self.mcp_controller = McpServerSettingsController(
            settings_provider=lambda: self.settings,
            config_manager=self.config_manager,
            collection_lookup=lambda collection_id: self.collections.collection_by_id(
                collection_id
            ),
            environment_lookup=lambda environment_id: self.env.environment_by_id(
                environment_id
            ),
            metrics=self.metrics,
            template_service=self.template_service,
            mcp_manager=mcp_manager,
            registry=mcp_registry,
        )
        self.tabs = TabsPresenter(
            self.request_manager,
            self.state_manager,
            self.settings,
            metrics=self.metrics,
            history_manager=self.history_manager,
            template_service=self.template_service,
            alert_manager=self._alert_manager,
        )
        self.env = EnvPresenter(
            self.storage,
            self.config_manager,
            self.mcp_controller.manager,
            self.settings,
            self.request_manager.get_collections,
            self.metrics,
            mcp_registry=self.mcp_controller.registry,
            state_manager=self.state_manager,
        )
        main_window_lifecycle.configure_env_update_consumer(self)
        self.mcp_controls = self.env.mcp_controls
        self.mcp_controls.set_server_controller(self.mcp_controller)
        self._build_layout()
        wire_presenter_signals(self)
        self._create_menu_bar()
        self._setup_shortcuts()
        self._startup_collections_ready = False
        self._startup_env_ready = False
        self._ui_ready = False
        self.collections.collections_loaded.connect(self._on_startup_collections_loaded)
        self.env.environments_loaded.connect(self._on_startup_environments_loaded)
        self._startup_settings_reapplied = False
        self.apply_settings(self.settings)
        if isinstance(self.config_manager.recovery_notice, ConfigRecoveryNotice):
            QTimer.singleShot(0, self._show_settings_recovery_notice)
        logger.info("main_window_initialized")
        if not defer_startup:
            self.start_initial_loads()

    def start_initial_loads(self) -> None:
        """Start background loads after the composition root owns this window."""
        if self._teardown_started:
            return
        self.collections.load_collections_async()
        self.env.load_environments()

    @property
    def is_ui_ready(self) -> bool:
        """True after startup collections+env loads and restore gate completed."""
        return self._ui_ready

    @property
    def settings(self) -> AppSettings:
        """The composition-root snapshot; its identity is stable for this window."""
        return self._settings

    def _on_startup_collections_loaded(self) -> None:
        if getattr(self, "_teardown_started", False):
            return
        self.collections.collections_loaded.disconnect(self._on_startup_collections_loaded)
        self._startup_collections_ready = True
        self._maybe_complete_startup_restore()

    def _on_startup_environments_loaded(self) -> None:
        if getattr(self, "_teardown_started", False):
            return
        self.env.environments_loaded.disconnect(self._on_startup_environments_loaded)
        self._startup_env_ready = True
        self._maybe_complete_startup_restore()

    def _maybe_complete_startup_restore(self) -> None:
        main_window_lifecycle.maybe_complete_startup_restore(self)

    def _load_icons(self) -> dict:
        d = Path(__file__).parent / "resources" / "icons"
        return {
            "collection": QIcon(str(d / "collection.svg")),
            "GET": QIcon(str(d / "method-get.svg")),
            "POST": QIcon(str(d / "method-post.svg")),
            "PUT": QIcon(str(d / "method-put.svg")),
            "DELETE": QIcon(str(d / "method-delete.svg")),
            "PATCH": QIcon(str(d / "method-patch.svg")),
        }

    def _build_layout(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        top_bar = QHBoxLayout()
        self.libraries_btn = QPushButton("Libraries")
        set_widget_id(self.libraries_btn, LIBRARY_MANAGER_BUTTON)
        self.libraries_btn.clicked.connect(self.open_library_manager)
        self.settings_btn = QPushButton("Settings")
        set_widget_id(self.settings_btn, SETTINGS_BUTTON)
        self.settings_btn.clicked.connect(self.open_settings)
        top_bar.addWidget(self.env.widget)
        top_bar.addWidget(self.libraries_btn)
        top_bar.addWidget(self.settings_btn)
        main_layout.addLayout(top_bar)
        splitter = QSplitter(Qt.Horizontal)
        self.history_panel = HistoryPanel(self.history_manager, icons=self.icons)
        sidebar = QTabWidget()
        sidebar.addTab(self.collections.panel, "Collections")
        sidebar.addTab(self.history_panel, "History")
        splitter.addWidget(sidebar)
        splitter.addWidget(self.tabs.widget)
        splitter.setSizes([300, 900])
        main_layout.addWidget(splitter)

    def _create_menu_bar(self) -> None:
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        lib_action = file_menu.addAction("Library Manager...")
        lib_action.triggered.connect(self.open_library_manager)
        quit_action = file_menu.addAction("Quit")
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.handle_exit)
        tag_action(
            quit_action,
            section="General",
            order=1,
            keys=("Ctrl+Q",),
            label="Quit Application",
        )
        help_menu = menubar.addMenu("Help")
        help_menu.addAction("Hotkeys").triggered.connect(self.handle_show_hotkeys)
        help_menu.addAction("About").triggered.connect(self.handle_show_about)

    def _setup_shortcuts(self) -> None:
        register_hotkey(
            self,
            section="General",
            label="Settings",
            keys=("Ctrl+,", "F12"),
            slot=self.open_settings,
            order=2,
        )
        register_hotkey(
            self,
            section="General",
            label="Environment Manager",
            keys=("Ctrl+E",),
            slot=self.env.handle_open_environments,
            order=3,
        )
        register_hotkey(
            self,
            section="Tabs",
            label="New Tab",
            keys=("Ctrl+N",),
            slot=lambda: self.tabs.handle_new_tab("shortcut"),
            order=1,
        )
        register_hotkey(
            self,
            section="Tabs",
            label="Close Tab",
            keys=("Ctrl+W",),
            slot=self.tabs.handle_close_tab,
            order=2,
        )
        register_hotkey(
            self,
            section="Tabs",
            label="Next Tab",
            keys=("Ctrl+Tab",),
            slot=self.tabs.handle_next_tab,
            order=3,
        )
        register_hotkey(
            self,
            section="Tabs",
            label="Previous Tab",
            keys=("Ctrl+Shift+Tab",),
            slot=self.tabs.handle_previous_tab,
            order=4,
        )
        register_hotkey_group(
            self,
            section="Tabs",
            label="Switch to Tab 1-9",
            bindings=tuple(
                (f"Alt+{index}", lambda idx=index - 1: self.tabs.handle_switch_to_tab(idx))
                for index in range(1, 10)
            ),
            order=5,
        )
        register_hotkey(
            self,
            section="Request Editor",
            label="Send Request",
            keys=("F5", "Ctrl+Return"),
            slot=self.tabs.handle_send_request_global,
            order=1,
        )
        register_hotkey(
            self,
            section="Request Editor",
            label="Focus URL Bar",
            keys=("Ctrl+L", "Alt+D"),
            slot=self.tabs.handle_focus_url,
            order=4,
        )
        register_hotkey(
            self,
            section="Request Editor",
            label="Switch to Params",
            keys=("Ctrl+P",),
            slot=self.tabs.handle_switch_to_params_global,
            order=5,
        )
        register_hotkey(
            self,
            section="Request Editor",
            label="Switch to Headers",
            keys=("Ctrl+H",),
            slot=self.tabs.handle_switch_to_headers_global,
            order=6,
        )
        register_hotkey(
            self,
            section="Request Editor",
            label="Switch to Body",
            keys=("Ctrl+B",),
            slot=self.tabs.handle_switch_to_body_global,
            order=7,
        )
        register_hotkey(
            self,
            section="Request Editor",
            label="Switch to Script",
            keys=("Ctrl+T",),
            slot=self.tabs.handle_switch_to_script_global,
            order=8,
        )
        register_protocol_session_hotkeys(self, self.tabs)

    def _alert_settings_changed(
        self, previous: AppSettings, updated: AppSettings
    ) -> bool:
        return main_window_lifecycle.alert_settings_changed(previous, updated)

    def _reload_alert_manager(self) -> None:
        main_window_lifecycle.reload_alert_manager(self, AlertManager)

    def apply_settings(self, settings: AppSettings) -> None:
        main_window_settings.apply_settings(self, settings)

    def open_settings(self) -> None:
        main_window_settings.open_settings(self, SettingsDialog)

    def _on_settings_persistence_failed(self, message: str) -> None:
        main_window_settings.show_persistence_failure(self, message)

    def _show_settings_recovery_notice(self) -> None:
        main_window_settings.show_recovery_notice(self)

    def _on_metrics_start_failed(self, message: str) -> None:
        if getattr(self, "_teardown_started", False):
            return
        logger.error("metrics_server_start_failed_ui message=%s", message)
        show_metrics_server_start_failed(self, message)

    def teardown(self, timeout_ms: int | None = None) -> TeardownResult:
        return main_window_lifecycle.teardown(self, timeout_ms)

    def _shutdown_for_exit(self) -> TeardownResult:
        return main_window_lifecycle.shutdown_for_exit(
            self, encryption_enabled_resolver=resolve_encryption_enabled
        )

    def closeEvent(self, event) -> None:
        logger.info("main_window_close_event")
        main_window_lifecycle.close_event(self, event)

    def handle_exit(self) -> None:
        logger.info("main_window_exit_requested")
        main_window_lifecycle.handle_exit(self)

    def open_library_manager(self) -> None:
        main_window_lifecycle.open_library_manager(self)

    def handle_show_hotkeys(self) -> None:
        main_window_lifecycle.show_hotkeys(self)

    def handle_show_about(self) -> None:
        main_window_lifecycle.show_about(self)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if getattr(self, "_teardown_started", False):
            return
        if self._startup_settings_reapplied:
            return
        self._startup_settings_reapplied = True
        # Re-apply settings after first show to survive Qt post-show style polish.
        QTimer.singleShot(0, lambda: self.apply_settings(self.settings))
