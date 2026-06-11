"""Settings persistence tests (PYPOST-125).

Covers ConfigManager JSON save/load with an isolated config directory and StateManager
delegation (expanded collections, open tabs, last environment) including no-op saves.
Includes restart-level integration for request_timeout via SettingsDialog (PYPOST-445).
"""

import pytest

pytestmark = pytest.mark.timeout(120)

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QApplication

from pypost.core.config_manager import ConfigManager
from pypost.core.state_manager import StateManager
from pypost.models.settings import AppSettings
from pypost.ui.dialogs.settings_dialog import SettingsDialog


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


class TestConfigManagerPersistence(unittest.TestCase):
    def test_load_missing_file_returns_defaults(self):
        with tempfile.TemporaryDirectory() as td:
            with patch("pypost.core.config_manager.user_config_dir", return_value=td):
                cm = ConfigManager()
                s = cm.load_config()
                self.assertIsInstance(s, AppSettings)
                self.assertEqual(s.revision, 0)

    def test_save_then_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            with patch("pypost.core.config_manager.user_config_dir", return_value=td):
                cm = ConfigManager()
                s = cm.load_config()
                s.font_size = 22
                s.metrics_port = 9099
                s.request_timeout = 120
                cm.save_config(s)

                cm2 = ConfigManager()
                s2 = cm2.load_config()
                self.assertEqual(s2.font_size, 22)
                self.assertEqual(s2.metrics_port, 9099)
                self.assertEqual(s2.request_timeout, 120)
                self.assertEqual(s2.revision, 1)

    def test_each_save_increments_revision(self):
        with tempfile.TemporaryDirectory() as td:
            with patch("pypost.core.config_manager.user_config_dir", return_value=td):
                cm = ConfigManager()
                s = cm.load_config()
                cm.save_config(s)
                cm.save_config(s)
                self.assertEqual(cm.load_config().revision, 2)

    def test_load_corrupt_file_returns_defaults(self):
        with tempfile.TemporaryDirectory() as td:
            cfg = Path(td) / "settings.json"
            cfg.write_text("not valid json", encoding="utf-8")
            with patch("pypost.core.config_manager.user_config_dir", return_value=td):
                s = ConfigManager().load_config()
                self.assertEqual(s, AppSettings())

    def test_load_legacy_settings_without_log_hidden_key_names_defaults_false(self):
        with tempfile.TemporaryDirectory() as td:
            cfg = Path(td) / "settings.json"
            cfg.write_text(
                '{"font_size": 12, "indent_size": 2, "request_timeout": 60, '
                '"config_version": 1, "revision": 0}',
                encoding="utf-8",
            )
            with patch("pypost.core.config_manager.user_config_dir", return_value=td):
                s = ConfigManager().load_config()
                self.assertFalse(s.log_hidden_key_names)

    def test_load_legacy_settings_without_encryption_fields_default_none(self):
        with tempfile.TemporaryDirectory() as td:
            cfg = Path(td) / "settings.json"
            cfg.write_text(
                '{"font_size": 12, "indent_size": 2, "request_timeout": 60, '
                '"config_version": 1, "revision": 0, "log_hidden_key_names": false}',
                encoding="utf-8",
            )
            with patch("pypost.core.config_manager.user_config_dir", return_value=td):
                s = ConfigManager().load_config()
                self.assertIsNone(s.env_encryption_enabled)
                self.assertIsNone(s.env_encryption_key_source)


class TestStateManagerPersistence(unittest.TestCase):
    def _cm_and_td(self):
        td = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(td, ignore_errors=True))
        patcher = patch("pypost.core.config_manager.user_config_dir", return_value=td)
        patcher.start()
        self.addCleanup(patcher.stop)
        return ConfigManager(), td

    def test_set_expanded_collections_persists(self):
        cm, _td = self._cm_and_td()
        sm = StateManager(cm)
        sm.set_expanded_collections(["c1", "c2"])
        sm.flush_pending_save()

        cm2 = ConfigManager()
        sm2 = StateManager(cm2)
        self.assertEqual(sm2.get_expanded_collections(), ["c1", "c2"])

    def test_set_open_tabs_persists(self):
        cm, _td = self._cm_and_td()
        sm = StateManager(cm)
        sm.set_open_tabs(["r1", "r2"])
        sm.flush_pending_save()

        sm2 = StateManager(ConfigManager())
        self.assertEqual(sm2.get_open_tabs(), ["r1", "r2"])

    def test_set_last_environment_id_persists(self):
        cm, _td = self._cm_and_td()
        sm = StateManager(cm)
        sm.set_last_environment_id("env-99")
        sm.flush_pending_save()

        sm2 = StateManager(ConfigManager())
        self.assertEqual(sm2.get_last_environment_id(), "env-99")

    def test_set_expanded_collections_noop_skips_save(self):
        cm, _td = self._cm_and_td()
        sm = StateManager(cm)
        with patch.object(cm, "save_config", wraps=cm.save_config) as wrapped:
            sm.set_expanded_collections([])
            wrapped.assert_not_called()
            sm.set_expanded_collections(["a"])
            wrapped.assert_not_called()
            sm.flush_pending_save()
            self.assertEqual(wrapped.call_count, 1)
            sm.set_expanded_collections(["a"])
            self.assertEqual(wrapped.call_count, 1)
            sm.flush_pending_save()
            self.assertEqual(wrapped.call_count, 1)

    def test_rapid_ui_state_changes_coalesce_to_single_save(self):
        cm, _td = self._cm_and_td()
        sm = StateManager(cm)
        with patch.object(cm, "save_config", wraps=cm.save_config) as wrapped:
            sm.set_expanded_collections(["a"])
            sm.set_expanded_collections(["a", "b"])
            sm.set_expanded_collections(["b"])
            sm.set_open_tabs(["r1"])
            sm.set_open_tabs(["r1", "r2"])
            wrapped.assert_not_called()
            sm.flush_pending_save()
            self.assertEqual(wrapped.call_count, 1)

        sm2 = StateManager(ConfigManager())
        self.assertEqual(sm2.get_expanded_collections(), ["b"])
        self.assertEqual(sm2.get_open_tabs(), ["r1", "r2"])


def test_request_timeout_survives_settings_dialog_save_and_restart(qapp):  # noqa: ARG001
    """PYPOST-445: Settings UI save path persists request_timeout across restart."""
    changed_timeout = 135
    with tempfile.TemporaryDirectory() as td:
        with patch("pypost.core.config_manager.user_config_dir", return_value=td):
            cm = ConfigManager()
            dlg = SettingsDialog(cm.load_config())
            try:
                dlg.timeout_spin.setValue(changed_timeout)
                dlg.accept()
                saved = dlg.get_settings()
                assert saved is not None
                assert saved.request_timeout == changed_timeout
                cm.save_config(saved)
            finally:
                dlg.close()

            cfg_path = Path(td) / "settings.json"
            on_disk = json.loads(cfg_path.read_text(encoding="utf-8"))
            assert on_disk["request_timeout"] == changed_timeout

            reloaded = ConfigManager().load_config()
            assert reloaded.request_timeout == changed_timeout

            dlg_after_restart = SettingsDialog(reloaded)
            try:
                assert dlg_after_restart.timeout_spin.value() == changed_timeout
            finally:
                dlg_after_restart.close()


if __name__ == "__main__":
    unittest.main()
