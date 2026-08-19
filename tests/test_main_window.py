import pytest

pytestmark = pytest.mark.timeout(60)

import logging
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QTabWidget, QWidget

from pypost.models.settings import AppSettings, McpServerConfiguration
from pypost.ui.main_window import MainWindow
from pypost.ui.mcp_server_controller import McpServerSettingsController

CONTROLLER_LOGGER = "pypost.ui.mcp_server_controller"

@pytest.mark.usefixtures("qapp")

class TestMainWindow(unittest.TestCase):
    def _make_mcp_controller(self, settings, registry, config_manager):
        """PYPOST-1071: persistence/lifecycle moved to McpServerSettingsController."""
        return McpServerSettingsController(
            settings_provider=lambda: settings,
            config_manager=config_manager,
            collection_lookup=lambda _collection_id: None,
            environment_lookup=lambda _environment_id: None,
            metrics=MagicMock(),
            template_service=MagicMock(),
            mcp_manager=MagicMock(),
            registry=registry,
        )

    def test_running_mcp_edit_persists_only_after_registry_commits(self):
        previous = McpServerConfiguration(
            id="server", port=1081, collection_id="collection", environment_id="environment"
        )
        replacement = previous.model_copy(update={"port": 1082})
        registry = MagicMock()
        registry.is_running.return_value = True
        settings = AppSettings(mcp_servers=[previous])
        config_manager = MagicMock()
        controller = self._make_mcp_controller(settings, registry, config_manager)

        controller.upsert_mcp_server(replacement)

        registry.reconfigure.assert_called_once_with("server", replacement)
        self.assertEqual(settings.mcp_servers, [previous])
        config_manager.save_config.assert_not_called()

        registry.list_configurations.return_value = [replacement]
        controller._on_mcp_server_reconfiguration_finished("server", True)

        self.assertEqual(settings.mcp_servers, [replacement])
        config_manager.save_config.assert_called_once_with(settings)

    def test_startup_logs_persisted_mcp_server_counts_without_endpoint_details(self):
        """PYPOST-1071 observability: startup evidence is counts only, never endpoints."""
        settings = AppSettings(
            mcp_servers=[
                McpServerConfiguration(
                    id="alpha",
                    port=1081,
                    collection_id="c1",
                    environment_id="e1",
                    enabled=True,
                ),
                McpServerConfiguration(
                    id="beta",
                    port=1082,
                    collection_id="c2",
                    environment_id="e2",
                    enabled=False,
                ),
            ]
        )
        with self.assertLogs(CONTROLLER_LOGGER, level=logging.INFO) as caplog:
            self._make_mcp_controller(settings, MagicMock(), MagicMock())

        loaded = [
            record.message
            for record in caplog.records
            if "mcp_persisted_servers_loaded" in record.message
        ]
        self.assertEqual(len(loaded), 1)
        self.assertIn("count=2", loaded[0])
        self.assertIn("enabled_count=1", loaded[0])
        for secret in ("alpha", "beta", "1081", "1082"):
            self.assertNotIn(secret, loaded[0])

    def test_persisted_mcp_mutations_log_their_reason(self):
        """PYPOST-1071 observability: every settings write names the mutation."""
        settings = AppSettings(
            mcp_servers=[
                McpServerConfiguration(
                    id="server",
                    port=1081,
                    collection_id="c1",
                    environment_id="e1",
                    enabled=False,
                )
            ]
        )
        registry = MagicMock()
        registry.is_running.return_value = False
        controller = self._make_mcp_controller(settings, registry, MagicMock())

        with self.assertLogs(CONTROLLER_LOGGER, level=logging.INFO) as caplog:
            controller.start_mcp_server("server")
            controller.stop_mcp_server("server")
            controller.remove_mcp_server("server")

        reasons = [
            record.message
            for record in caplog.records
            if "mcp_servers_persist_requested" in record.message
        ]
        self.assertEqual(len(reasons), 3)
        self.assertIn("reason=start count=1", reasons[0])
        self.assertIn("reason=stop count=1", reasons[1])
        self.assertIn("reason=remove count=0", reasons[2])

    def test_uncommitted_reconfiguration_is_logged_and_not_persisted(self):
        """PYPOST-1071 observability: a rolled-back edit must not look like a save."""
        configuration = McpServerConfiguration(
            id="server", port=1081, collection_id="c1", environment_id="e1"
        )
        settings = AppSettings(mcp_servers=[configuration])
        config_manager = MagicMock()
        controller = self._make_mcp_controller(settings, MagicMock(), config_manager)

        with self.assertLogs(CONTROLLER_LOGGER, level=logging.INFO) as caplog:
            controller._on_mcp_server_reconfiguration_finished("server", False)

        self.assertTrue(
            any(
                "mcp_server_reconfigure_finished" in record.message
                and "committed=false" in record.message
                for record in caplog.records
            )
        )
        self.assertFalse(
            any(
                "mcp_servers_persist_requested" in record.message
                for record in caplog.records
            )
        )
        config_manager.save_config.assert_not_called()

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
            patch("pypost.ui.mcp_server_controller.MCPServerManager"),
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
                history_manager=MagicMock(),
            )
            window.settings_btn = MagicMock()

        mock_collections.load_collections_async.assert_called_once()
        mock_collections.refresh_tree.assert_not_called()
        mock_collections.load_collections.assert_not_called()

    def test_post_load_starts_enabled_mcp_servers_only_after_both_sources_load(self):
        collections = SimpleNamespace(
            collections_loaded=MagicMock(), restore_tree_state=MagicMock()
        )
        environments = SimpleNamespace(environments_loaded=MagicMock())
        controller = MagicMock()
        window = SimpleNamespace(
            collections=collections,
            env=environments,
            tabs=SimpleNamespace(restore_tabs=MagicMock()),
            mcp_controller=controller,
            _startup_collections_ready=False,
            _startup_env_ready=False,
            _ui_ready=False,
        )
        window._maybe_complete_startup_restore = lambda: MainWindow._maybe_complete_startup_restore(
            window
        )
        window._on_startup_collections_loaded = lambda: MainWindow._on_startup_collections_loaded(
            window
        )
        window._on_startup_environments_loaded = lambda: MainWindow._on_startup_environments_loaded(
            window
        )

        MainWindow._on_startup_collections_loaded(window)

        controller.start_enabled.assert_not_called()
        MainWindow._on_startup_environments_loaded(window)

        controller.start_enabled.assert_called_once()
        collections.restore_tree_state.assert_called_once()
        window.tabs.restore_tabs.assert_called_once()
        assert window._ui_ready is True

    def test_constructor_stores_injected_dependencies(self):
        """PYPOST-382 / PYPOST-695: metrics, template_service, config_manager, alert_manager,
        history_manager, storage, request_manager, mcp_manager are retained."""
        metrics = MagicMock()
        template_service = MagicMock()
        config_manager = MagicMock()
        alert_manager = MagicMock()
        history_manager = MagicMock()
        storage = MagicMock()
        request_manager = MagicMock()
        mcp_manager = MagicMock()
        with (
            patch("pypost.ui.main_window.StateManager") as mock_sm,
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
                history_manager=history_manager,
                storage=storage,
                request_manager=request_manager,
                mcp_manager=mcp_manager,
            )
        self.assertIs(metrics, window.metrics)
        self.assertIs(template_service, window.template_service)
        self.assertIs(config_manager, window.config_manager)
        self.assertIs(alert_manager, window._alert_manager)
        self.assertIs(history_manager, window.history_manager)
        self.assertIs(storage, window.storage)
        self.assertIs(mcp_manager, window.mcp_controller.manager)
        self.assertFalse(hasattr(window, "mcp_manager"))
        self.assertFalse(hasattr(window, "mcp_registry"))
        self.assertFalse(hasattr(McpServerSettingsController, "for_window"))
        storage.apply_encryption_settings.assert_not_called()

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
            patch("pypost.ui.mcp_server_controller.MCPServerManager"),
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
            mock_collections.panel = QWidget()
            mock_tabs.widget = QWidget()
            mock_env_cls.return_value.widget = QWidget()
            window = MainWindow(
                metrics=metrics,
                template_service=template_service,
                history_manager=MagicMock(),
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
            mock_collections.panel = QWidget()
            
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
