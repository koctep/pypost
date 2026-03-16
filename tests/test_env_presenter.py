import unittest
from unittest.mock import MagicMock
from PySide6.QtWidgets import QApplication, QWidget

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

    def __init__(self):
        self.started = []
        self.stopped = 0
        self._running = False

    def start_server(self, port, tools, host="127.0.0.1"):
        self.started.append((port, host, tools))
        self._running = True

    def stop_server(self):
        self.stopped += 1
        self._running = False

    def is_running(self):
        return self._running


def _make_mcp_manager():
    mgr = FakeMCPManager()
    mgr.status_changed = MagicMock()
    mgr.status_changed.connect = MagicMock()
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
        get_collections = lambda: (collections or [])
        return EnvPresenter(storage, config, mcp, settings, get_collections)

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

    def test_env_keys_changed_emitted(self):
        env = _make_env("e1", "Dev", {"A": "1", "B": "2"})
        p = self._make_presenter([env])
        received = []
        p.env_keys_changed.connect(received.append)
        p._environments = [env]
        p.env_selector.addItem(env.name, env)
        p._on_env_changed(1)
        self.assertIn(sorted(received[-1]), [["A", "B"]])

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

    def test_load_environments_emits_no_signal_for_no_env(self):
        p = self._make_presenter([])
        received = []
        p.env_variables_changed.connect(received.append)
        p.load_environments()
        # stays at index 0 (No Environment), on_env_changed NOT triggered for index 0
        self.assertEqual(len(received), 0)


if __name__ == "__main__":
    unittest.main()
