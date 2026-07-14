import logging
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from pypost.core.alert_manager import AlertManager
from pypost.core.config_manager import ConfigManager
from pypost.core.encryption_config import resolve_encryption_enabled
from pypost.core.history_manager import HistoryManager
from pypost.core.mcp_server import MCPServerManager
from pypost.core.metrics import MetricsManager
from pypost.core.request_manager import RequestManager
from pypost.core.state_manager import StateManager
from pypost.core.storage import StorageManager
from pypost.ui.styles.style_manager import StyleManager
from pypost.core.template_service import TemplateService
from pypost.models.settings import AppSettings
from pypost.ui.collection_item_dialogs import show_metrics_server_start_failed
from pypost.ui.dialogs.about_dialog import AboutDialog
from pypost.ui.dialogs.hotkeys_dialog import HotkeysDialog
from pypost.ui.hotkeys import register_hotkey, register_hotkey_group, tag_action
from pypost.ui.dialogs.settings_dialog import SettingsDialog
from pypost.ui.main_window_signals import wire_presenter_signals
from pypost.ui.presenters import CollectionsPresenter, EnvPresenter, TabsPresenter
from pypost.ui.widgets.history_panel import HistoryPanel

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(
        self,
        metrics: MetricsManager,
        template_service: TemplateService,
        config_manager: ConfigManager | None = None,
        alert_manager: AlertManager | None = None,
    ) -> None:
        super().__init__()
        self.setWindowTitle("PyPost")
        self.resize(1200, 800)
        self.metrics = metrics
        self.metrics.connect_start_failed(self._on_metrics_start_failed)
        self.template_service = template_service
        self.storage = StorageManager(metrics=self.metrics)
        if config_manager is not None:
            logger.debug("config_manager_source source=injected")
            self.config_manager = config_manager
        else:
            logger.debug("config_manager_source source=new")
            self.config_manager = ConfigManager()
        self._alert_manager = alert_manager
        logger.debug("MainWindow: alert_manager_injected=%s", alert_manager is not None)
        self.request_manager = RequestManager(self.storage, defer_initial_load=True)
        self.state_manager = StateManager(self.config_manager, parent=self)
        self.storage.apply_encryption_settings(self.state_manager.settings)
        self.style_manager = StyleManager()
        self.mcp_manager = MCPServerManager(
            metrics=self.metrics, template_service=self.template_service
        )
        self.settings = self.state_manager.settings
        self.icons = self._load_icons()
        self.history_manager = HistoryManager()
        self.collections = CollectionsPresenter(
            self.request_manager,
            self.state_manager,
            self.metrics,
            self.icons,
            storage=self.storage,
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
            self.mcp_manager,
            self.settings,
            self.request_manager.get_collections,
            self.metrics,
        )
        self._build_layout()
        wire_presenter_signals(self)
        self._create_menu_bar()
        self._setup_shortcuts()
        self._startup_collections_ready = False
        self._startup_env_ready = False
        self.collections.collections_loaded.connect(self._on_startup_collections_loaded)
        self.env.environments_loaded.connect(self._on_startup_environments_loaded)
        self.collections.load_collections_async()
        self.env.load_environments()
        self._startup_settings_reapplied = False
        self.apply_settings(self.settings)
        logger.info("main_window_initialized")

    def _on_startup_collections_loaded(self) -> None:
        self.collections.collections_loaded.disconnect(self._on_startup_collections_loaded)
        self._startup_collections_ready = True
        self._maybe_complete_startup_restore()

    def _on_startup_environments_loaded(self) -> None:
        self.env.environments_loaded.disconnect(self._on_startup_environments_loaded)
        self._startup_env_ready = True
        self._maybe_complete_startup_restore()

    def _maybe_complete_startup_restore(self) -> None:
        if not (self._startup_collections_ready and self._startup_env_ready):
            return
        self.tabs.restore_tabs()
        self.collections.restore_tree_state()

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
        self.settings_btn = QPushButton("Settings")
        self.settings_btn.clicked.connect(self.open_settings)
        top_bar.addWidget(self.env.widget)
        top_bar.addWidget(self.settings_btn)
        main_layout.addLayout(top_bar)
        splitter = QSplitter(Qt.Horizontal)
        self.history_panel = HistoryPanel(self.history_manager, icons=self.icons)
        sidebar = QTabWidget()
        sidebar.addTab(self.collections.widget, "Collections")
        sidebar.addTab(self.history_panel, "History")
        splitter.addWidget(sidebar)
        splitter.addWidget(self.tabs.widget)
        splitter.setSizes([300, 900])
        main_layout.addWidget(splitter)

    def _create_menu_bar(self) -> None:
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
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

    def _alert_settings_changed(
        self, previous: AppSettings, updated: AppSettings
    ) -> bool:
        return (
            previous.alert_log_path != updated.alert_log_path
            or previous.alert_webhook_url != updated.alert_webhook_url
            or previous.alert_webhook_auth_header != updated.alert_webhook_auth_header
        )

    def _reload_alert_manager(self) -> None:
        if self._alert_manager is not None:
            self._alert_manager.close()
        log_path = (
            Path(self.settings.alert_log_path) if self.settings.alert_log_path else None
        )
        self._alert_manager = AlertManager(
            log_path=log_path,
            webhook_url=self.settings.alert_webhook_url,
            webhook_auth_header=self.settings.alert_webhook_auth_header,
        )
        self.tabs.set_alert_manager(self._alert_manager)
        logger.info(
            "alert_manager_reloaded log_path=%s webhook_url_set=%s",
            log_path,
            bool(self.settings.alert_webhook_url),
        )

    def apply_settings(self, settings: AppSettings) -> None:
        self.settings = settings
        logger.debug("apply_settings_start font_size=%d", settings.font_size)
        app = QApplication.instance()
        if app:
            self.style_manager.apply_theme(app, settings.theme)
            self.style_manager.apply_styles(app, font_size=settings.font_size)
            font = app.font()
            font.setPointSize(settings.font_size)
            app.setFont(font)
            logger.debug(
                "apply_settings_font_applied point_size=%d", app.font().pointSize()
            )
        self.tabs.apply_settings(settings)
        self.env.apply_settings(settings)

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.settings, self, storage=self.storage)
        if not dialog.exec():
            return
        new_settings = dialog.get_settings()
        if not new_settings:
            return
        previous_settings = self.settings
        metrics_changed = (
            previous_settings.metrics_host != new_settings.metrics_host
            or previous_settings.metrics_port != new_settings.metrics_port
        )
        alert_settings_changed = self._alert_settings_changed(
            previous_settings, new_settings
        )
        self.settings = new_settings
        self.config_manager.save_config(self.settings)
        self.env.wait_storage_idle()
        self.storage.apply_encryption_settings(self.settings)
        self.apply_settings(self.settings)
        if alert_settings_changed:
            self._reload_alert_manager()
        if metrics_changed:
            logger.info(
                "metrics_server_restarting host=%s port=%d",
                self.settings.metrics_host,
                self.settings.metrics_port,
            )
            self.metrics.restart_server(
                self.settings.metrics_host, self.settings.metrics_port
            )
        logger.info(
            "settings_applied font_size=%d indent_size=%d request_timeout=%d "
            "env_encryption_enabled=%s env_encryption_key_source=%s",
            self.settings.font_size,
            self.settings.indent_size,
            self.settings.request_timeout,
            self.settings.env_encryption_enabled,
            self.settings.env_encryption_key_source,
        )
        self.env.reload_current_env()

    def _on_metrics_start_failed(self, message: str) -> None:
        logger.error("metrics_server_start_failed_ui message=%s", message)
        show_metrics_server_start_failed(self, message)

    def handle_exit(self) -> None:
        logger.info("main_window_exit_requested")
        self.state_manager.flush_pending_save()
        if resolve_encryption_enabled(self.settings):
            idle = self.env.wait_storage_idle()
            logger.info("main_window_exit_storage_idle completed=%s", idle)
        QApplication.instance().quit()

    def handle_show_hotkeys(self) -> None:
        HotkeysDialog(self).exec()

    def handle_show_about(self) -> None:
        AboutDialog(self).exec()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self._startup_settings_reapplied:
            return
        self._startup_settings_reapplied = True
        # Re-apply settings after first show to survive Qt post-show style polish.
        QTimer.singleShot(0, lambda: self.apply_settings(self.settings))
