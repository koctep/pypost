import pytest

pytestmark = pytest.mark.timeout(60)

import unittest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication

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

    def test_startup_refreshes_tree_from_request_manager(self):
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
            patch("pypost.ui.main_window.MainWindow._wire_signals"),
            patch("pypost.ui.main_window.MainWindow._create_menu_bar"),
            patch("pypost.ui.main_window.MainWindow._setup_shortcuts"),
            patch("pypost.ui.main_window.MainWindow.apply_settings"),
            patch("pypost.ui.main_window.resolve_encryption_enabled", return_value=False),
        ):
            mock_sm.return_value.settings = AppSettings()
            window = MainWindow(
                metrics=metrics,
                template_service=template_service,
            )
            window.settings_btn = MagicMock()

        mock_collections.refresh_tree.assert_called_once()
        mock_collections.load_collections.assert_not_called()

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
