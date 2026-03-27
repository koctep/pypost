import logging

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QApplication,
)
from PySide6.QtGui import QIcon, QKeySequence, QShortcut
from PySide6.QtCore import Qt, QTimer
from pathlib import Path

from pypost.core.storage import StorageManager
from pypost.core.config_manager import ConfigManager
from pypost.core.style_manager import StyleManager
from pypost.core.request_manager import RequestManager
from pypost.core.state_manager import StateManager
from pypost.core.mcp_server import MCPServerManager
from pypost.core.metrics import MetricsManager
from pypost.core.history_manager import HistoryManager
from pypost.core.template_service import TemplateService
from pypost.core.alert_manager import AlertManager
from pypost.ui.dialogs.settings_dialog import SettingsDialog
from pypost.ui.dialogs.hotkeys_dialog import HotkeysDialog
from pypost.ui.dialogs.about_dialog import AboutDialog
from pypost.ui.presenters import CollectionsPresenter, TabsPresenter, EnvPresenter
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
        self.template_service = template_service
        self.storage = StorageManager()
        if config_manager is not None:
            logger.debug("config_manager_source source=injected")
            self.config_manager = config_manager
        else:
            logger.debug("config_manager_source source=new")
            self.config_manager = ConfigManager()
        self._alert_manager = alert_manager
        logger.debug("MainWindow: alert_manager_injected=%s", alert_manager is not None)
        self.request_manager = RequestManager(self.storage)
        self.state_manager = StateManager(self.config_manager)
        self.style_manager = StyleManager()
        self.mcp_manager = MCPServerManager(metrics=self.metrics,
                                            template_service=self.template_service)
        self.settings = self.state_manager.settings
        self.icons = self._load_icons()
        self.history_manager = HistoryManager()
        self.collections = CollectionsPresenter(
            self.request_manager, self.state_manager, self.metrics, self.icons,
        )
        self.tabs = TabsPresenter(
            self.request_manager, self.state_manager, self.settings,
            metrics=self.metrics,
            history_manager=self.history_manager,
            template_service=self.template_service,
            alert_manager=self._alert_manager,
        )
        self.env = EnvPresenter(
            self.storage, self.config_manager, self.mcp_manager,
            self.settings, self.request_manager.get_collections,
        )
        self._build_layout()
        self._wire_signals()
        self._create_menu_bar()
        self._setup_shortcuts()
        self.collections.load_collections()
        self.env.load_environments()
        self.tabs.restore_tabs()
        self.collections.restore_tree_state()
        self._startup_settings_reapplied = False
        self.apply_settings(self.settings)
        logger.info("main_window_initialized")

    def _load_icons(self) -> dict:
        d = Path(__file__).parent / 'resources' / 'icons'
        return {
            'collection': QIcon(str(d / 'collection.svg')),
            'GET': QIcon(str(d / 'method-get.svg')),
            'POST': QIcon(str(d / 'method-post.svg')),
            'PUT': QIcon(str(d / 'method-put.svg')),
            'DELETE': QIcon(str(d / 'method-delete.svg')),
            'PATCH': QIcon(str(d / 'method-patch.svg')),
        }

    def _build_layout(self) -> None:
        from PySide6.QtWidgets import QTabWidget
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

    def _wire_signals(self) -> None:
        self.collections.open_request_in_tab.connect(self.tabs.add_new_tab)
        self.collections.open_request_in_isolated_tab.connect(self.tabs.add_new_tab)
        self.collections.collections_changed.connect(self.env.load_environments)
        self.collections.request_renamed.connect(self.tabs.rename_request_tabs)
        self.env.env_variables_changed.connect(self.tabs.on_env_variables_changed)
        self.env.env_keys_changed.connect(self.tabs.on_env_keys_changed)
        self.tabs.variable_set_requested.connect(self.env.handle_variable_set_request)
        self.tabs.env_update_requested.connect(self.env.on_env_update)
        self.tabs.request_saved.connect(self.collections.load_collections)
        self.tabs.request_saved.connect(self.collections.restore_tree_state)
        self.tabs.request_executed.connect(self.history_panel.refresh)
        self.history_panel.load_into_editor.connect(self.tabs.load_request_from_history)

    def _create_menu_bar(self) -> None:
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        quit_action = file_menu.addAction("Quit")
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.handle_exit)
        help_menu = menubar.addMenu("Help")
        help_menu.addAction("Hotkeys").triggered.connect(self.handle_show_hotkeys)
        help_menu.addAction("About").triggered.connect(self.handle_show_about)

    def _setup_shortcuts(self) -> None:
        def sc(key, slot):
            QShortcut(QKeySequence(key), self).activated.connect(slot)
        sc("Ctrl+N", lambda: self.tabs.handle_new_tab("shortcut"))
        sc("Ctrl+W", self.tabs.handle_close_tab)
        sc("Ctrl+Tab", self.tabs.handle_next_tab)
        sc("Ctrl+Shift+Tab", self.tabs.handle_previous_tab)
        for i in range(1, 10):
            sc(f"Alt+{i}", lambda idx=i - 1: self.tabs.handle_switch_to_tab(idx))
        sc("Ctrl+,", self.open_settings)
        sc("F12", self.open_settings)
        sc("Ctrl+E", self.env.handle_open_environments)
        sc("Ctrl+L", self.tabs.handle_focus_url)
        sc("Alt+D", self.tabs.handle_focus_url)
        sc("F5", self.tabs.handle_send_request_global)
        sc("Ctrl+P", self.tabs.handle_switch_to_params_global)
        sc("Ctrl+H", self.tabs.handle_switch_to_headers_global)
        sc("Ctrl+B", self.tabs.handle_switch_to_body_global)
        sc("Ctrl+T", self.tabs.handle_switch_to_script_global)

    def apply_settings(self, settings) -> None:
        self.settings = settings
        logger.debug("apply_settings_start font_size=%d", settings.font_size)
        app = QApplication.instance()
        if app:
            self.style_manager.apply_styles(app)
            font = app.font()
            font.setPointSize(settings.font_size)
            app.setFont(font)
            logger.debug("apply_settings_font_applied point_size=%d", app.font().pointSize())
            for w in [
                self.collections.widget, self.env.env_selector, self.tabs.widget,
                self.env.manage_btn, self.settings_btn, self.env.env_label,
                self.tabs.widget.tabBar(),
            ]:
                w.setFont(font)
            if self.menuBar():
                self.menuBar().setFont(font)
        self.tabs.apply_settings(settings)

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.settings, self)
        if not dialog.exec():
            return
        new_settings = dialog.get_settings()
        if not new_settings:
            return
        metrics_changed = (
            self.settings.metrics_host != new_settings.metrics_host
            or self.settings.metrics_port != new_settings.metrics_port
        )
        self.settings = new_settings
        self.config_manager.save_config(self.settings)
        self.apply_settings(self.settings)
        if metrics_changed:
            logger.info(
                "metrics_server_restarting host=%s port=%d",
                self.settings.metrics_host, self.settings.metrics_port,
            )
            self.metrics.restart_server(self.settings.metrics_host, self.settings.metrics_port)
        logger.info(
            "settings_applied font_size=%d indent_size=%d request_timeout=%d",
            self.settings.font_size,
            self.settings.indent_size,
            self.settings.request_timeout,
        )
        self.env._on_env_changed(self.env.env_selector.currentIndex())

    def handle_exit(self) -> None:
        logger.info("main_window_exit_requested")
        QApplication.instance().quit()

    def handle_show_hotkeys(self) -> None:
        HotkeysDialog(self).exec()

    def handle_show_about(self) -> None:
        AboutDialog(self).exec()

    def keyPressEvent(self, event) -> None:
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Return:
            self.tabs.handle_send_request_global()
            event.accept()
            return
        super().keyPressEvent(event)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self._startup_settings_reapplied:
            return
        self._startup_settings_reapplied = True
        # Re-apply settings after first show to survive Qt post-show style polish.
        QTimer.singleShot(0, lambda: self.apply_settings(self.settings))
