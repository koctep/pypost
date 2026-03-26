"""Settings persistence tests (PYPOST-125).

Covers ConfigManager JSON save/load with an isolated config directory and StateManager
delegation (expanded collections, open tabs, last environment) including no-op saves.
"""

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pypost.core.config_manager import ConfigManager
from pypost.core.state_manager import StateManager
from pypost.models.settings import AppSettings


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
                cm.save_config(s)

                cm2 = ConfigManager()
                s2 = cm2.load_config()
                self.assertEqual(s2.font_size, 22)
                self.assertEqual(s2.metrics_port, 9099)
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

        cm2 = ConfigManager()
        sm2 = StateManager(cm2)
        self.assertEqual(sm2.get_expanded_collections(), ["c1", "c2"])

    def test_set_open_tabs_persists(self):
        cm, _td = self._cm_and_td()
        sm = StateManager(cm)
        sm.set_open_tabs(["r1", "r2"])

        sm2 = StateManager(ConfigManager())
        self.assertEqual(sm2.get_open_tabs(), ["r1", "r2"])

    def test_set_last_environment_id_persists(self):
        cm, _td = self._cm_and_td()
        sm = StateManager(cm)
        sm.set_last_environment_id("env-99")

        sm2 = StateManager(ConfigManager())
        self.assertEqual(sm2.get_last_environment_id(), "env-99")

    def test_set_expanded_collections_noop_skips_save(self):
        cm, _td = self._cm_and_td()
        sm = StateManager(cm)
        with patch.object(cm, "save_config", wraps=cm.save_config) as wrapped:
            sm.set_expanded_collections([])
            wrapped.assert_not_called()
            sm.set_expanded_collections(["a"])
            self.assertEqual(wrapped.call_count, 1)
            sm.set_expanded_collections(["a"])
            self.assertEqual(wrapped.call_count, 1)


if __name__ == "__main__":
    unittest.main()
