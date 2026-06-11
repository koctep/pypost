import pytest

pytestmark = pytest.mark.timeout(60)

import logging
import unittest
from unittest.mock import MagicMock, patch

from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication, QWidget, QInputDialog

from pypost.core.key_provider import EnvironmentEncryptionError
from pypost.core.mcp_activity_log import McpActivityEntry, McpActivityLog
from pypost.ui.presenters.env_presenter import EnvPresenter
from pypost.models.models import Environment, Collection, RequestData
from pypost.models.settings import AppSettings


def _make_env(env_id: str, name: str, variables=None, enable_mcp=False) -> Environment:
    return Environment(id=env_id, name=name, variables=variables or {}, enable_mcp=enable_mcp)


class FakeStorage:
    def __init__(self, environments=None):
        self._environments = environments or []
        self.saved = []

    def load_environments(self):
        return list(self._environments)

    def save_environments(self, envs):
        self.saved.append(list(envs))


class FakeConfigManager:
    def __init__(self):
        self.saved = []

    def save_config(self, settings):
        self.saved.append(settings)


class FakeMCPManager:
    status_changed = MagicMock()
    start_failed = MagicMock()
    activity_recorded = MagicMock()

    def __init__(self):
        self.started = []
        self.stopped = 0
        self._running = False
        self.activity_log = McpActivityLog()

    def start_server(self, port, tools, host="127.0.0.1"):
        self.started.append((port, host, tools))
        self._running = True

    def stop_server(self):
        self.stopped += 1
        self._running = False

    def is_running(self):
        return self._running

    def set_variable_supplier(self, supplier):
        self.variable_supplier = supplier

    def set_hidden_keys_supplier(self, supplier):
        self.hidden_keys_supplier = supplier


def _make_mcp_manager():
    mgr = FakeMCPManager()
    mgr.status_changed = MagicMock()
    mgr.status_changed.connect = MagicMock()
    mgr.start_failed = MagicMock()
    mgr.start_failed.connect = MagicMock()
    mgr.activity_recorded = MagicMock()
    mgr.activity_recorded.connect = MagicMock()
    return mgr


class TestEnvPresenter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _make_presenter(self, environments=None, collections=None):
        storage = FakeStorage(environments)
        config = FakeConfigManager()
        mcp = _make_mcp_manager()
        settings = AppSettings()
        metrics = MagicMock()  # Mock metrics manager

        def get_collections():
            return collections or []

        return EnvPresenter(storage, config, mcp, settings, get_collections, metrics)

    def test_widget_is_qwidget(self):
        p = self._make_presenter()
        self.assertIsInstance(p.widget, QWidget)

    def test_load_environments_populates_combo(self):
        envs = [_make_env("e1", "Production"), _make_env("e2", "Staging")]
        p = self._make_presenter(envs)
        p.load_environments()
        # "No Environment" + 2 envs = 3 items
        self.assertEqual(p.env_selector.count(), 3)
        self.assertEqual(p.env_selector.itemText(1), "Production")
        self.assertEqual(p.env_selector.itemText(2), "Staging")

    def test_load_environments_selects_last_used(self):
        envs = [_make_env("e1", "Dev"), _make_env("e2", "Prod")]
        p = self._make_presenter(envs)
        p._settings.last_environment_id = "e2"
        p.load_environments()
        # index 0 = No Env, index 1 = Dev, index 2 = Prod
        self.assertEqual(p.env_selector.currentIndex(), 2)

    def test_load_environments_defaults_to_no_environment(self):
        p = self._make_presenter([])
        p.load_environments()
        self.assertEqual(p.env_selector.currentIndex(), 0)

    def test_env_variables_changed_emitted_on_selection(self):
        env = _make_env("e1", "Dev", {"KEY": "VALUE"})
        p = self._make_presenter([env])
        received = []
        p.env_variables_changed.connect(received.append)
        p.load_environments()
        # selection restored triggers signal; but since last_env not set, stays at 0
        # manually select env 1
        p._on_env_changed(1)
        self.assertEqual(len(received), 1)
        self.assertEqual(received[-1], {"KEY": "VALUE"})

    def test_reload_current_env_refreshes_current_selection(self):
        env = _make_env("e1", "Dev", {"KEY": "VALUE"})
        p = self._make_presenter([env])
        p._environments = [env]
        p.env_selector.blockSignals(True)
        p.env_selector.addItem(env.name, env)
        p.env_selector.setCurrentIndex(1)
        p.env_selector.blockSignals(False)
        received = []
        p.env_variables_changed.connect(received.append)
        p.reload_current_env()
        self.assertEqual(received[-1], {"KEY": "VALUE"})

    def test_env_keys_changed_emitted(self):
        env = _make_env("e1", "Dev", {"A": "1", "B": "2"})
        p = self._make_presenter([env])
        received = []
        p.env_keys_changed.connect(received.append)
        p._environments = [env]
        p.env_selector.addItem(env.name, env)
        p._on_env_changed(1)
        self.assertIn(sorted(received[-1]), [["A", "B"]])

    def test_env_hidden_keys_changed_emitted(self):
        env = Environment(
            id="e1",
            name="Dev",
            variables={"TOKEN": "abc"},
            hidden_keys={"TOKEN"},
        )
        p = self._make_presenter([env])
        received = []
        p.env_hidden_keys_changed.connect(received.append)
        p._environments = [env]
        p.env_selector.blockSignals(True)
        p.env_selector.addItem(env.name, env)
        p.env_selector.blockSignals(False)
        p._on_env_changed(1)
        self.assertEqual(received[-1], {"TOKEN"})

    def test_hidden_keys_supplier_returns_current_hidden_keys(self):
        env = Environment(
            id="e1",
            name="Dev",
            variables={"TOKEN": "abc"},
            hidden_keys={"TOKEN"},
        )
        p = self._make_presenter([env])
        p._environments = [env]
        p.env_selector.blockSignals(True)
        p.env_selector.addItem(env.name, env)
        p.env_selector.blockSignals(False)
        p._on_env_changed(1)
        self.assertEqual(p._mcp_manager.hidden_keys_supplier(), {"TOKEN"})

    def test_on_env_changed_no_environment_emits_empty_dict(self):
        p = self._make_presenter([])
        received = []
        p.env_variables_changed.connect(received.append)
        p._on_env_changed(0)
        self.assertEqual(received[-1], {})

    def test_on_env_changed_stops_mcp_for_no_environment(self):
        env = _make_env("e1", "Dev", enable_mcp=True)
        p = self._make_presenter([env])
        p._environments = [env]
        p.env_selector.blockSignals(True)
        p.env_selector.addItem(env.name, env)
        p.env_selector.blockSignals(False)
        p._on_env_changed(0)
        self.assertEqual(p._mcp_manager.stopped, 1)

    def test_on_env_changed_starts_mcp_when_enabled(self):
        env = _make_env("e1", "MCP-Env", enable_mcp=True)
        p = self._make_presenter([env])
        p._settings.mcp_port = 1080
        p._settings.mcp_host = "127.0.0.1"
        p._environments = [env]
        p.env_selector.blockSignals(True)
        p.env_selector.addItem(env.name, env)
        p.env_selector.blockSignals(False)
        p._on_env_changed(1)
        self.assertEqual(len(p._mcp_manager.started), 1)
        self.assertEqual(p._mcp_manager.started[0][0], 1080)

    def test_mcp_tools_filtered_by_expose_flag(self):
        req_exposed = RequestData(id="r1", name="Tool", expose_as_mcp=True)
        req_hidden = RequestData(id="r2", name="Hidden", expose_as_mcp=False)
        col = Collection(id="c1", name="API", requests=[req_exposed, req_hidden])
        p = self._make_presenter(collections=[col])
        tools = p._get_mcp_tools()
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0].id, "r1")

    def test_current_variables_returns_empty_for_no_environment(self):
        p = self._make_presenter([])
        self.assertEqual(p.current_variables, {})

    def test_current_variables_returns_env_variables(self):
        env = _make_env("e1", "Dev", {"TOKEN": "abc"})
        p = self._make_presenter([env])
        p._environments = [env]
        p.env_selector.blockSignals(True)
        p.env_selector.addItem(env.name, env)
        p.env_selector.setCurrentIndex(1)
        p.env_selector.blockSignals(False)
        self.assertEqual(p.current_variables, {"TOKEN": "abc"})

    def test_on_env_update_merges_variables(self):
        env = _make_env("e1", "Dev", {"A": "1"})
        p = self._make_presenter([env])
        p._environments = [env]
        p.env_selector.blockSignals(True)
        p.env_selector.addItem(env.name, env)
        p.env_selector.setCurrentIndex(1)
        p.env_selector.blockSignals(False)
        p.on_env_update({"B": "2"})
        self.assertEqual(env.variables, {"A": "1", "B": "2"})

    def test_handle_variable_set_request_saves_to_env(self):
        env = _make_env("e1", "Dev", {"EXISTING": "val"})
        p = self._make_presenter([env])
        p._environments = [env]
        p.env_selector.blockSignals(True)
        p.env_selector.addItem(env.name, env)
        p.env_selector.setCurrentIndex(1)
        p.env_selector.blockSignals(False)
        p.handle_variable_set_request("NEW_KEY", "new_value")
        self.assertEqual(env.variables["NEW_KEY"], "new_value")

    def test_mcp_status_label_updated_on_running(self):
        p = self._make_presenter([])
        p._on_mcp_status_changed(True)
        self.assertIn("ON", p.mcp_status_label.text())

    def test_mcp_status_label_updated_on_stopped(self):
        p = self._make_presenter([])
        p._on_mcp_status_changed(False)
        self.assertEqual(p.mcp_status_label.text(), "MCP: OFF")

    def test_mcp_tools_button_shows_count(self):
        req = RequestData(id="r1", name="Tool", expose_as_mcp=True)
        col = Collection(id="c1", name="API", requests=[req])
        p = self._make_presenter(collections=[col])
        p._refresh_mcp_tools_button()
        self.assertEqual(p.mcp_tools_btn.text(), "MCP Tools (1)")

    def test_mcp_activity_button_shows_count(self):
        p = self._make_presenter([])
        p._mcp_manager.activity_log.append(McpActivityEntry.new_list_tools(2))
        p._refresh_mcp_activity_button()
        self.assertEqual(p.mcp_activity_btn.text(), "MCP Activity (1)")

    def test_mcp_activity_recorded_updates_button(self):
        p = self._make_presenter([])
        p._mcp_manager.activity_log.append(McpActivityEntry.new_list_tools(1))
        p._on_mcp_activity_recorded(McpActivityEntry.new_list_tools(99))
        self.assertEqual(p.mcp_activity_btn.text(), "MCP Activity (1)")

    def test_on_env_changed_shows_starting_when_mcp_enabled(self):
        env = _make_env("e1", "MCP-Env", enable_mcp=True)
        p = self._make_presenter([env])
        p._settings.mcp_port = 1080
        p._settings.mcp_host = "127.0.0.1"
        p._environments = [env]
        p.env_selector.blockSignals(True)
        p.env_selector.addItem(env.name, env)
        p.env_selector.blockSignals(False)
        p._on_env_changed(1)
        self.assertIn("Starting", p.mcp_status_label.text())

    def test_mcp_start_failed_shows_warning(self):
        p = self._make_presenter([])
        shown = []

        def capture_warning(parent, message):
            shown.append((parent, message))

        with patch(
            "pypost.ui.presenters.env_presenter.show_mcp_server_start_failed",
            side_effect=capture_warning,
        ):
            p._on_mcp_start_failed("Port is busy")
        self.assertEqual(p.mcp_status_label.text(), "MCP: OFF")
        self.assertEqual(len(shown), 1)
        self.assertIn("Port is busy", shown[0][1])

    def test_valid_variable_name_does_not_emit_debug_log(self):
        p = self._make_presenter()
        with self.assertNoLogs("pypost.ui.presenters.env_presenter", level=logging.DEBUG):
            is_valid, _ = p._is_valid_variable_name("valid_name")
        self.assertTrue(is_valid)

    def test_invalid_variable_name_emits_debug_log(self):
        p = self._make_presenter()
        with self.assertLogs("pypost.ui.presenters.env_presenter", level=logging.DEBUG) as caplog:
            is_valid, _ = p._is_valid_variable_name("1invalid")
        self.assertFalse(is_valid)
        self.assertEqual(len(caplog.records), 1)
        self.assertIn("variable_name_validation_attempt", caplog.records[0].message)
        self.assertIn("valid=False", caplog.records[0].message)

    def test_handle_variable_set_request_valid_name(self):
        """Test that valid variable names are accepted"""
        env = _make_env("e1", "Dev", {})
        p = self._make_presenter([env])
        p._environments = [env]
        p.env_selector.blockSignals(True)
        p.env_selector.addItem(env.name, env)
        p.env_selector.setCurrentIndex(1)
        p.env_selector.blockSignals(False)

        # Mock QInputDialog to return a valid name
        original_getText = QInputDialog.getText
        QInputDialog.getText = lambda *args, **kwargs: ("valid_name", True)

        try:
            p.handle_variable_set_request(None, "test_value")
            self.assertIn("valid_name", env.variables)
            self.assertEqual(env.variables["valid_name"], "test_value")
        finally:
            QInputDialog.getText = original_getText

    def test_handle_variable_set_request_empty_name(self):
        """Test that empty variable names are rejected"""
        env = _make_env("e1", "Dev", {})
        p = self._make_presenter([env])
        p._environments = [env]
        p.env_selector.blockSignals(True)
        p.env_selector.addItem(env.name, env)
        p.env_selector.setCurrentIndex(1)
        p.env_selector.blockSignals(False)

        # Mock QInputDialog to return empty string after stripping
        original_getText = QInputDialog.getText
        QInputDialog.getText = lambda *args, **kwargs: ("   ", True)  # spaces only

        warning_called = []

        def mock_warning(parent, error_msg):
            warning_called.append(error_msg)

        with patch(
            "pypost.ui.presenters.env_presenter.show_invalid_variable_name_error",
            side_effect=mock_warning,
        ):
            try:
                p.handle_variable_set_request(None, "test_value")
            finally:
                QInputDialog.getText = original_getText

        self.assertNotIn("", env.variables)
        self.assertTrue(len(warning_called) > 0)
        self.assertIn("Variable name cannot be empty.", warning_called[0])

    def test_handle_variable_set_request_starts_with_digit(self):
        """Test that variable names starting with digit are rejected"""
        env = _make_env("e1", "Dev", {})
        p = self._make_presenter([env])
        p._environments = [env]
        p.env_selector.blockSignals(True)
        p.env_selector.addItem(env.name, env)
        p.env_selector.setCurrentIndex(1)
        p.env_selector.blockSignals(False)

        # Mock QInputDialog to return name starting with digit
        original_getText = QInputDialog.getText
        QInputDialog.getText = lambda *args, **kwargs: ("1invalid", True)

        warning_called = []

        def mock_warning(parent, error_msg):
            warning_called.append(error_msg)

        with patch(
            "pypost.ui.presenters.env_presenter.show_invalid_variable_name_error",
            side_effect=mock_warning,
        ):
            try:
                p.handle_variable_set_request(None, "test_value")
            finally:
                QInputDialog.getText = original_getText

        self.assertNotIn("1invalid", env.variables)
        self.assertTrue(len(warning_called) > 0)
        self.assertIn("Variable name cannot start with a digit.", warning_called[0])

    def test_handle_variable_set_request_invalid_chars(self):
        """Test that variable names with invalid characters are rejected"""
        env = _make_env("e1", "Dev", {})
        p = self._make_presenter([env])
        p._environments = [env]
        p.env_selector.blockSignals(True)
        p.env_selector.addItem(env.name, env)
        p.env_selector.setCurrentIndex(1)
        p.env_selector.blockSignals(False)

        # Mock QInputDialog to return name with invalid chars
        original_getText = QInputDialog.getText
        QInputDialog.getText = lambda *args, **kwargs: ("valid-name", True)  # hyphen is invalid

        warning_called = []

        def mock_warning(parent, error_msg):
            warning_called.append(error_msg)

        with patch(
            "pypost.ui.presenters.env_presenter.show_invalid_variable_name_error",
            side_effect=mock_warning,
        ):
            try:
                p.handle_variable_set_request(None, "test_value")
            finally:
                QInputDialog.getText = original_getText

        self.assertNotIn("valid-name", env.variables)
        self.assertTrue(len(warning_called) > 0)
        self.assertIn(
            "Variable name can only contain letters, numbers, and underscores.",
            warning_called[0],
        )

    def test_handle_variable_set_request_cancelled_dialog(self):
        """Test that cancelled dialog does nothing"""
        env = _make_env("e1", "Dev", {})
        p = self._make_presenter([env])
        p._environments = [env]
        p.env_selector.blockSignals(True)
        p.env_selector.addItem(env.name, env)
        p.env_selector.setCurrentIndex(1)
        p.env_selector.blockSignals(False)

        # Mock QInputDialog to return cancelled
        original_getText = QInputDialog.getText
        QInputDialog.getText = lambda *args, **kwargs: ("", False)

        try:
            p.handle_variable_set_request(None, "test_value")
            # Should not have added the variable
            self.assertEqual(len(env.variables), 0)
        finally:
            QInputDialog.getText = original_getText

    def test_load_environments_emits_no_signal_for_no_env(self):
        p = self._make_presenter([])
        received = []
        p.env_variables_changed.connect(received.append)
        p.load_environments()
        # stays at index 0 (No Environment), on_env_changed NOT triggered for index 0
        self.assertEqual(len(received), 0)

    def test_apply_settings_updates_settings_reference(self):
        p = self._make_presenter([])
        new_settings = AppSettings(log_hidden_key_names=True)
        p.apply_settings(new_settings)
        self.assertIs(p._settings, new_settings)
        self.assertTrue(p._settings.log_hidden_key_names)

    def test_async_load_refreshes_combo_when_encryption_enabled(self):
        envs = [_make_env("e1", "Production")]
        p = self._make_presenter(envs)
        p._settings = AppSettings(env_encryption_enabled=True)
        loaded = []
        p.environments_loaded.connect(lambda: loaded.append(True))
        p.load_environments()

        loop = QEventLoop()
        timer = QTimer()
        timer.setInterval(10)

        def check_done():
            if loaded:
                loop.quit()

        timer.timeout.connect(check_done)
        timer.start()
        loop.exec()
        timer.stop()

        self.assertEqual(len(loaded), 1)
        self.assertEqual(p.env_selector.count(), 2)
        self.assertEqual(p.env_selector.itemText(1), "Production")

    def test_save_failure_shows_warning_dialog(self):
        p = self._make_presenter([])
        shown = []

        def capture_warning(parent, message):
            shown.append((parent, message))

        with patch(
            "pypost.ui.presenters.env_presenter.show_env_save_failed",
            side_effect=capture_warning,
        ):
            p._on_storage_save_failed(
                EnvironmentEncryptionError("Encryption key is unavailable.")
            )

        self.assertEqual(len(shown), 1)
        self.assertIn("Encryption key is unavailable.", shown[0][1])

    def test_sync_save_used_when_encryption_disabled(self):
        env = _make_env("e1", "Dev", {"K": "V"})
        p = self._make_presenter([env])
        p._environments = [env]
        p.env_selector.blockSignals(True)
        p.env_selector.addItem(env.name, env)
        p.env_selector.setCurrentIndex(1)
        p.env_selector.blockSignals(False)
        with patch.object(p._storage_gateway, "save_async") as save_async:
            p._save_environments()
            save_async.assert_not_called()
        self.assertEqual(len(p._storage.saved), 1)


if __name__ == "__main__":
    unittest.main()
