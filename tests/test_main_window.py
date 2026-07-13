import pytest

pytestmark = pytest.mark.timeout(60)

import unittest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication, QTabWidget, QWidget

from pypost.models.settings import AppSettings
from pypost.ui.main_window import MainWindow


class TestMainWindow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_main_window_has_no_collection_delete_flow_methods(self):
        """PYPOST-326: delete flow lives in CollectionTreeActions, not MainWindow."""
        delete_flow_names = {
            "show_collection_item_context_menu",
            "show_context_menu",
            "handle_delete",
            "confirm_delete",
            "handle_delete_collection_item",
        }
        for name in delete_flow_names:
            self.assertFalse(
                hasattr(MainWindow, name),
                f"MainWindow should not define {name}",
            )

    def test_startup_dispatches_async_collection_load(self):
        metrics = MagicMock()
        template_service = MagicMock()
        mock_collections = MagicMock()
        with (
            patch("pypost.ui.main_window.StorageManager"),
            patch("pypost.ui.main_window.ConfigManager"),
            patch("pypost.ui.main_window.RequestManager"),
            patch("pypost.ui.main_window.StateManager") as mock_sm,
            patch("pypost.ui.main_window.MCPServerManager"),
            patch("pypost.ui.main_window.HistoryManager"),
            patch("pypost.ui.main_window.CollectionsPresenter", return_value=mock_collections),
            patch("pypost.ui.main_window.TabsPresenter"),
            patch("pypost.ui.main_window.EnvPresenter"),
            patch("pypost.ui.main_window.HistoryPanel"),
            patch("pypost.ui.main_window.MainWindow._build_layout"),
            patch("pypost.ui.main_window.wire_presenter_signals"),
            patch("pypost.ui.main_window.MainWindow._create_menu_bar"),
            patch("pypost.ui.main_window.MainWindow._setup_shortcuts"),
            patch("pypost.ui.main_window.MainWindow.apply_settings"),
        ):
            mock_sm.return_value.settings = AppSettings()
            window = MainWindow(
                metrics=metrics,
                template_service=template_service,
            )
            window.settings_btn = MagicMock()

        mock_collections.load_collections_async.assert_called_once()
        mock_collections.refresh_tree.assert_not_called()
        mock_collections.load_collections.assert_not_called()

    def test_constructor_stores_injected_dependencies(self):
        """PYPOST-382: metrics, template_service, config_manager, alert_manager are retained."""
        metrics = MagicMock()
        template_service = MagicMock()
        config_manager = MagicMock()
        alert_manager = MagicMock()
        with (
            patch("pypost.ui.main_window.StorageManager"),
            patch("pypost.ui.main_window.ConfigManager"),
            patch("pypost.ui.main_window.RequestManager"),
            patch("pypost.ui.main_window.StateManager") as mock_sm,
            patch("pypost.ui.main_window.MCPServerManager"),
            patch("pypost.ui.main_window.HistoryManager"),
            patch("pypost.ui.main_window.CollectionsPresenter"),
            patch("pypost.ui.main_window.TabsPresenter"),
            patch("pypost.ui.main_window.EnvPresenter"),
            patch("pypost.ui.main_window.HistoryPanel"),
            patch("pypost.ui.main_window.MainWindow._build_layout"),
            patch("pypost.ui.main_window.wire_presenter_signals"),
            patch("pypost.ui.main_window.MainWindow._create_menu_bar"),
            patch("pypost.ui.main_window.MainWindow._setup_shortcuts"),
            patch("pypost.ui.main_window.MainWindow.apply_settings"),
            patch("pypost.ui.main_window.resolve_encryption_enabled", return_value=False),
        ):
            mock_sm.return_value.settings = AppSettings()
            window = MainWindow(
                metrics=metrics,
                template_service=template_service,
                config_manager=config_manager,
                alert_manager=alert_manager,
            )
        self.assertIs(metrics, window.metrics)
        self.assertIs(template_service, window.template_service)
        self.assertIs(config_manager, window.config_manager)
        self.assertIs(alert_manager, window._alert_manager)

    def test_build_layout_sidebar_is_qtabwidget(self):
        """PYPOST-61: left sidebar uses QTabWidget with Collections and History tabs."""
        metrics = MagicMock()
        template_service = MagicMock()
        mock_collections = MagicMock()
        mock_tabs = MagicMock()
        with (
            patch("pypost.ui.main_window.StorageManager"),
            patch("pypost.ui.main_window.ConfigManager"),
            patch("pypost.ui.main_window.RequestManager"),
            patch("pypost.ui.main_window.StateManager") as mock_sm,
            patch("pypost.ui.main_window.MCPServerManager"),
            patch("pypost.ui.main_window.HistoryManager"),
            patch(
                "pypost.ui.main_window.CollectionsPresenter",
                return_value=mock_collections,
            ),
            patch("pypost.ui.main_window.TabsPresenter", return_value=mock_tabs),
            patch("pypost.ui.main_window.EnvPresenter") as mock_env_cls,
            patch("pypost.ui.main_window.HistoryPanel", return_value=QWidget()),
            patch("pypost.ui.main_window.wire_presenter_signals"),
            patch("pypost.ui.main_window.MainWindow._create_menu_bar"),
            patch("pypost.ui.main_window.MainWindow._setup_shortcuts"),
            patch("pypost.ui.main_window.MainWindow.apply_settings"),
            patch(
                "pypost.ui.main_window.resolve_encryption_enabled",
                return_value=False,
            ),
        ):
            mock_sm.return_value.settings = AppSettings()
            mock_collections.widget = QWidget()
            mock_tabs.widget = QWidget()
            mock_env_cls.return_value.widget = QWidget()
            window = MainWindow(
                metrics=metrics,
                template_service=template_service,
            )
            splitter = window.centralWidget().layout().itemAt(1).widget()
            sidebar = splitter.widget(0)
            self.assertIsInstance(sidebar, QTabWidget)
            self.assertEqual(sidebar.tabText(0), "Collections")
            self.assertEqual(sidebar.tabText(1), "History")

    def test_main_window_curl_copied_status_bar(self):
        metrics = MagicMock()
        template_service = MagicMock()
        config_manager = MagicMock()
        
        with patch("pypost.ui.main_window.CollectionsPresenter") as MockCollections, \
             patch("pypost.ui.main_window.TabsPresenter") as MockTabs, \
             patch("pypost.ui.main_window.EnvPresenter") as MockEnv:
            
            from PySide6.QtWidgets import QWidget, QTabWidget
            
            mock_collections = MockCollections.return_value
            mock_collections.widget = QWidget()
            
            mock_tabs = MockTabs.return_value
            mock_tabs.widget = QTabWidget()
            
            mock_env = MockEnv.return_value
            mock_env.widget = QWidget()
            
            window = MainWindow(metrics=metrics, template_service=template_service, config_manager=config_manager)
            
            with patch.object(window.statusBar(), "showMessage") as mock_show_message:
                # Emit the signal from the history panel
                window.history_panel.curl_copied.emit()
                
                mock_show_message.assert_called_once_with("Copied to clipboard", 3000)

if __name__ == "__main__":
    unittest.main()
