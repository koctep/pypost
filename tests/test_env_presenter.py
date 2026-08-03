import pytest

pytestmark = pytest.mark.timeout(60)

import logging
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QApplication, QWidget, QInputDialog

from pypost.core.key_provider import EnvironmentEncryptionError
from pypost.core.mcp_activity_log import McpActivityEntry, McpActivityLog
from pypost.core.mcp_server_registry import MCPServerRegistry
from pypost.ui.presenters.env_presenter import EnvPresenter
from pypost.models.models import Environment, Collection, RequestData
from pypost.models.settings import AppSettings, McpServerConfiguration
from tests.helpers.process_until import process_until

_REPO_ROOT = Path(__file__).resolve().parents[1]

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

    def serialize_environment_records(
        self,
        environments,
        *,
        target_envelope_version=None,
    ):
        return [env.model_dump(mode="json") for env in environments]


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

    def update_tools(self, tools):
        if not self._running:
            return False
        self.started.append(
            (self.started[-1][0], self.started[-1][1], tools)
        )
        return True

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

@pytest.mark.usefixtures("qapp")

class TestEnvPresenter(unittest.TestCase):
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

    def test_registry_status_summary_reports_running_and_failed_instances(self):
        registry = MCPServerRegistry(
            collection_lookup=lambda _id: None,
            environment_lookup=lambda _id: None,
        )
        p = EnvPresenter(
            FakeStorage(),
            FakeConfigManager(),
            _make_mcp_manager(),
            AppSettings(),
            lambda: [],
            MagicMock(),
            mcp_registry=registry,
        )
        registry.upsert(
            McpServerConfiguration(
                id="first", port=1081, collection_id="collection", environment_id="environment"
            )
        )
        registry.upsert(
            McpServerConfiguration(
                id="second", port=1082, collection_id="collection", environment_id="environment"
            )
        )
        registry._set_status("first", "running")
        registry._set_status("second", "failed", "port unavailable")

        self.assertEqual(p.mcp_status_text(), "MCP Servers: 1 running; 1 failed")

    def test_load_environments_populates_combo(self):
        envs = [_make_env("e1", "Production"), _make_env("e2", "Staging")]
        p = self._make_presenter(envs)
        p.load_environments()
        # "No Environment" + 2 envs = 3 items
        self.assertEqual(p.environment_count(), 3)
        self.assertEqual(p.environment_display_name_at(1), "Production")
        self.assertEqual(p.environment_display_name_at(2), "Staging")

    def test_load_environments_selects_last_used(self):
        envs = [_make_env("e1", "Dev"), _make_env("e2", "Prod")]
        p = self._make_presenter(envs)
        p._settings.last_environment_id = "e2"
        p.load_environments()
        # index 0 = No Env, index 1 = Dev, index 2 = Prod
        self.assertEqual(p.current_environment_index(), 2)

    def test_load_environments_defaults_to_no_environment(self):
        p = self._make_presenter([])
        p.load_environments()
        self.assertEqual(p.current_environment_index(), 0)

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
        p._env_selector.blockSignals(True)
        p._env_selector.addItem(env.name, env)
        p._env_selector.setCurrentIndex(1)
        p._env_selector.blockSignals(False)
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
        p._env_selector.addItem(env.name, env)
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
        p._env_selector.blockSignals(True)
        p._env_selector.addItem(env.name, env)
        p._env_selector.blockSignals(False)
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
        p._env_selector.blockSignals(True)
        p._env_selector.addItem(env.name, env)
        p._env_selector.blockSignals(False)
        p._on_env_changed(1)
        self.assertEqual(p._mcp_manager.hidden_keys_supplier(), {"TOKEN"})

    def test_registers_variable_supplier_on_init(self):
        p = self._make_presenter([])
        self.assertIsNotNone(p._mcp_manager.variable_supplier)
        self.assertEqual(p._mcp_manager.variable_supplier(), {})

    def test_supplier_returns_current_variables_after_env_change(self):
        env_dev = _make_env("e1", "Dev", {"A": "1"})
        env_prod = _make_env("e2", "Prod", {"B": "2"})
        p = self._make_presenter([env_dev, env_prod])
        p.load_environments()
        p._on_env_changed(1)
        self.assertEqual(p._mcp_manager.variable_supplier(), {"A": "1"})
        p._on_env_changed(2)
        self.assertEqual(p._mcp_manager.variable_supplier(), {"B": "2"})

    def test_tracks_mcp_active_env_changed_when_switching_while_running(self):
        env_dev = _make_env("e1", "Dev", {"A": "1"}, enable_mcp=True)
        env_prod = _make_env("e2", "Prod", {"B": "2"}, enable_mcp=True)
        p = self._make_presenter([env_dev, env_prod])
        p._environments = [env_dev, env_prod]
        p._env_selector.blockSignals(True)
        p._env_selector.addItem(env_dev.name, env_dev)
        p._env_selector.addItem(env_prod.name, env_prod)
        p._env_selector.blockSignals(False)
        p._on_env_changed(1)
        p._on_env_changed(2)
        p._metrics.track_mcp_active_env_changed.assert_called_once()

    def test_does_not_track_mcp_active_env_changed_on_same_env_refresh(self):
        env = _make_env("e1", "Dev", {"A": "1"}, enable_mcp=True)
        p = self._make_presenter([env])
        p._environments = [env]
        p._env_selector.blockSignals(True)
        p._env_selector.addItem(env.name, env)
        p._env_selector.blockSignals(False)
        p._on_env_changed(1)
        env.variables["A"] = "2"
        p._on_env_changed(1)
        p._metrics.track_mcp_active_env_changed.assert_not_called()

    def test_tracks_mcp_active_env_changed_when_deselecting_while_running(self):
        env = _make_env("e1", "Dev", enable_mcp=True)
        p = self._make_presenter([env])
        p._environments = [env]
        p._env_selector.blockSignals(True)
        p._env_selector.addItem(env.name, env)
        p._env_selector.blockSignals(False)
        p._on_env_changed(1)
        with self.assertLogs("pypost.ui.presenters.env_presenter", level=logging.INFO) as caplog:
            p._on_env_changed(0)
        p._metrics.track_mcp_active_env_changed.assert_called_once()
        self.assertTrue(any("mcp_active_env_changed" in r.message for r in caplog.records))

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
        p._env_selector.blockSignals(True)
        p._env_selector.addItem(env.name, env)
        p._env_selector.blockSignals(False)
        p._on_env_changed(0)
        self.assertEqual(p._mcp_manager.stopped, 1)

    def test_on_env_changed_starts_mcp_when_enabled(self):
        env = _make_env("e1", "MCP-Env", enable_mcp=True)
        p = self._make_presenter([env])
        p._settings.mcp_port = 1080
        p._settings.mcp_host = "127.0.0.1"
        p._environments = [env]
        p._env_selector.blockSignals(True)
        p._env_selector.addItem(env.name, env)
        p._env_selector.blockSignals(False)
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
        p._env_selector.blockSignals(True)
        p._env_selector.addItem(env.name, env)
        p._env_selector.setCurrentIndex(1)
        p._env_selector.blockSignals(False)
        self.assertEqual(p.current_variables, {"TOKEN": "abc"})

    def test_on_env_update_merges_variables(self):
        env = _make_env("e1", "Dev", {"A": "1"})
        p = self._make_presenter([env])
        p._environments = [env]
        p._env_selector.blockSignals(True)
        p._env_selector.addItem(env.name, env)
        p._env_selector.setCurrentIndex(1)
        p._env_selector.blockSignals(False)
        p.on_env_update({"B": "2"})
        self.assertEqual(env.variables, {"A": "1", "B": "2"})

    def test_handle_variable_set_request_saves_to_env(self):
        env = _make_env("e1", "Dev", {"EXISTING": "val"})
        p = self._make_presenter([env])
        p._environments = [env]
        p._env_selector.blockSignals(True)
        p._env_selector.addItem(env.name, env)
        p._env_selector.setCurrentIndex(1)
        p._env_selector.blockSignals(False)
        p.handle_variable_set_request("NEW_KEY", "new_value")
        self.assertEqual(env.variables["NEW_KEY"], "new_value")

    def test_mcp_status_label_updated_on_running(self):
        p = self._make_presenter([])
        p._on_mcp_status_changed(True)
        self.assertIn("ON", p.mcp_status_text())

    def test_mcp_status_label_updated_on_stopped(self):
        p = self._make_presenter([])
        p._on_mcp_status_changed(False)
        self.assertEqual(p.mcp_status_text(), "MCP: OFF")

    def test_mcp_tools_button_shows_count(self):
        req = RequestData(id="r1", name="Tool", expose_as_mcp=True)
        col = Collection(id="c1", name="API", requests=[req])
        p = self._make_presenter(collections=[col])
        p._refresh_mcp_tools_button()
        self.assertEqual(p.mcp_tools_button_text(), "MCP Tools (1)")

    def test_refresh_mcp_tools_restarts_when_running(self):
        env = _make_env("e1", "MCP-Env", enable_mcp=True)
        req = RequestData(id="r1", name="Tool", expose_as_mcp=True)
        col = Collection(id="c1", name="API", requests=[req])
        p = self._make_presenter([env], collections=[col])
        p._environments = [env]
        p._env_selector.blockSignals(True)
        p._env_selector.addItem(env.name, env)
        p._env_selector.setCurrentIndex(1)
        p._env_selector.blockSignals(False)
        p._on_env_changed(1)
        self.assertEqual(len(p._mcp_manager.started), 1)

        req2 = RequestData(id="r2", name="NewTool", expose_as_mcp=True)
        col.requests.append(req2)

        p.refresh_mcp_tools()
        self.assertEqual(len(p._mcp_manager.started), 2)
        self.assertEqual(p.mcp_tools_button_text(), "MCP Tools (2)")

    def test_refresh_mcp_tools_noop_when_mcp_disabled(self):
        req = RequestData(id="r1", name="Tool", expose_as_mcp=True)
        col = Collection(id="c1", name="API", requests=[req])
        p = self._make_presenter(collections=[col])
        p.refresh_mcp_tools()
        self.assertEqual(len(p._mcp_manager.started), 0)
        self.assertEqual(p.mcp_tools_button_text(), "MCP Tools (1)")

    def test_mcp_activity_button_shows_count(self):
        p = self._make_presenter([])
        p._mcp_manager.activity_log.append(McpActivityEntry.new_list_tools(2))
        p._refresh_mcp_activity_button()
        self.assertEqual(p.mcp_activity_button_text(), "MCP Activity (1)")

    def test_mcp_activity_recorded_updates_button(self):
        p = self._make_presenter([])
        p._mcp_manager.activity_log.append(McpActivityEntry.new_list_tools(1))
        p._on_mcp_activity_recorded(McpActivityEntry.new_list_tools(99))
        self.assertEqual(p.mcp_activity_button_text(), "MCP Activity (1)")

    def test_on_env_changed_shows_starting_when_mcp_enabled(self):
        env = _make_env("e1", "MCP-Env", enable_mcp=True)
        p = self._make_presenter([env])
        p._settings.mcp_port = 1080
        p._settings.mcp_host = "127.0.0.1"
        p._environments = [env]
        p._env_selector.blockSignals(True)
        p._env_selector.addItem(env.name, env)
        p._env_selector.blockSignals(False)
        p._on_env_changed(1)
        self.assertIn("Starting", p.mcp_status_text())

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
        self.assertEqual(p.mcp_status_text(), "MCP: OFF")
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
        p._env_selector.blockSignals(True)
        p._env_selector.addItem(env.name, env)
        p._env_selector.setCurrentIndex(1)
        p._env_selector.blockSignals(False)

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
        p._env_selector.blockSignals(True)
        p._env_selector.addItem(env.name, env)
        p._env_selector.setCurrentIndex(1)
        p._env_selector.blockSignals(False)

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
        p._env_selector.blockSignals(True)
        p._env_selector.addItem(env.name, env)
        p._env_selector.setCurrentIndex(1)
        p._env_selector.blockSignals(False)

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
        p._env_selector.blockSignals(True)
        p._env_selector.addItem(env.name, env)
        p._env_selector.setCurrentIndex(1)
        p._env_selector.blockSignals(False)

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
        p._env_selector.blockSignals(True)
        p._env_selector.addItem(env.name, env)
        p._env_selector.setCurrentIndex(1)
        p._env_selector.blockSignals(False)

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

    @patch("pypost.ui.presenters.env_presenter.EnvironmentDialog")
    def test_open_env_manager_passes_storage_serializer_directly(self, mock_dialog):
        p = self._make_presenter([])
        mock_dialog.return_value.environments = []

        p._open_env_manager()

        serializer = mock_dialog.call_args.kwargs["serialize_export_records"]
        self.assertIs(serializer.__self__, p._storage)
        self.assertIs(
            serializer.__func__,
            p._storage.serialize_environment_records.__func__,
        )

    def test_widget_properties_removed(self):
        p = self._make_presenter([])
        for name in (
            "env_selector",
            "manage_btn",
            "mcp_activity_btn",
            "mcp_tools_btn",
            "mcp_status_label",
            "env_label",
        ):
            self.assertFalse(hasattr(type(p), name), f"property {name} should be removed")

    def test_async_load_refreshes_combo_when_encryption_enabled(self):
        envs = [_make_env("e1", "Production")]
        p = self._make_presenter(envs)
        p._settings = AppSettings(env_encryption_enabled=True)
        loaded = []
        p.environments_loaded.connect(lambda: loaded.append(True))
        p.load_environments()

        process_until(lambda: bool(loaded), timeout_ms=5_000)

        self.assertEqual(len(loaded), 1)
        self.assertEqual(p.environment_count(), 2)
        self.assertEqual(p.environment_display_name_at(1), "Production")

    @pytest.mark.timeout(15)
    def test_async_load_wait_exits_near_deadline_when_never_complete(self):
        """Async-load wait fails near wall-clock deadline (PYPOST-877).

        Never-true predicate must exit in ~300 ms with AssertionError via
        shared ``process_until`` (wall-clock + posted quit). Run in a
        subprocess so a hang cannot wedge the parent pytest process.
        """
        child = r"""
import sys
import time
from pathlib import Path

repo = Path(r"%s")
sys.path.insert(0, str(repo))

from PySide6.QtWidgets import QApplication

from tests.helpers.process_until import process_until

app = QApplication.instance() or QApplication([])
started = time.monotonic()
try:
    process_until(lambda: False, timeout_ms=300)
except AssertionError as exc:
    if "condition not met within 300ms" not in str(exc):
        print("BAD_MESSAGE:", exc, file=sys.stderr)
        raise SystemExit(2)
    elapsed_s = time.monotonic() - started
    if elapsed_s >= 2.0:
        print(f"TOO_SLOW: {elapsed_s:.2f}s", file=sys.stderr)
        raise SystemExit(3)
    raise SystemExit(0)
else:
    print("NO_ASSERTION", file=sys.stderr)
    raise SystemExit(4)
""" % (_REPO_ROOT,)
        env = {
            **os.environ,
            "QT_QPA_PLATFORM": "offscreen",
            "PYTHONPATH": os.pathsep.join(
                [str(_REPO_ROOT), *os.environ.get("PYTHONPATH", "").split(os.pathsep)]
            ),
        }
        try:
            result = subprocess.run(
                [sys.executable, "-c", child],
                timeout=2.0,
                capture_output=True,
                text=True,
                env=env,
                cwd=str(_REPO_ROOT),
            )
        except subprocess.TimeoutExpired:
            self.fail(
                "async-load wait hung past wall-clock deadline "
                "(expected AssertionError within ~300ms via process_until)"
            )
        self.assertEqual(
            result.returncode,
            0,
            f"stdout={result.stdout!r} stderr={result.stderr!r}",
        )

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
        p._env_selector.blockSignals(True)
        p._env_selector.addItem(env.name, env)
        p._env_selector.setCurrentIndex(1)
        p._env_selector.blockSignals(False)
        with patch.object(p._storage_gateway, "save_async") as save_async:
            p._save_environments()
            save_async.assert_not_called()
        self.assertEqual(len(p._storage.saved), 1)

if __name__ == "__main__":
    unittest.main()
