import unittest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication

from pypost.ui.main_window import MainWindow

class TestMainWindow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

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
