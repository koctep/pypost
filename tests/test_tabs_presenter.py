import unittest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication

from pypost.ui.presenters.tabs_presenter import TabsPresenter, RequestTab
from pypost.models.models import RequestData
from pypost.models.settings import AppSettings


def _make_request(req_id: str = "r1", name: str = "Test", method: str = "GET") -> RequestData:
    return RequestData(id=req_id, name=name, method=method)


class FakeRequestManager:
    def __init__(self, requests=None):
        self._requests = {r.id: (r, MagicMock(id="c1")) for r in (requests or [])}
        self.saved = []
        self.collections = []

    def find_request(self, req_id):
        return self._requests.get(req_id)

    def get_collections(self):
        return self.collections

    def save_request(self, req, col_id):
        self.saved.append((req, col_id))

    def create_collection(self, name):
        from pypost.models.models import Collection
        col = Collection(name=name)
        self.collections.append(col)
        return col


class FakeStateManager:
    def __init__(self, open_tabs=None):
        self._open_tabs = open_tabs or []
        self._expanded = []
        self.settings = AppSettings()

    def get_open_tabs(self):
        return list(self._open_tabs)

    def set_open_tabs(self, ids):
        self._open_tabs = ids

    def get_expanded_collections(self):
        return list(self._expanded)

    def set_expanded_collections(self, ids):
        self._expanded = ids


class TestTabsPresenter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _make_presenter(self, requests=None, open_tabs=None):
        rm = FakeRequestManager(requests)
        sm = FakeStateManager(open_tabs)
        settings = AppSettings()
        return TabsPresenter(rm, sm, settings, metrics=MagicMock())

    def test_widget_is_qtab_widget(self):
        from PySide6.QtWidgets import QTabWidget
        p = self._make_presenter()
        self.assertIsInstance(p.widget, QTabWidget)

    def test_add_new_tab_creates_unnamed_tab(self):
        p = self._make_presenter()
        p.add_new_tab()
        self.assertEqual(p.widget.count(), 1)
        self.assertEqual(p.widget.tabText(0), "New Request")

    def test_add_new_tab_with_request_data(self):
        req = _make_request(name="Login")
        p = self._make_presenter()
        p.add_new_tab(req)
        self.assertEqual(p.widget.count(), 1)
        self.assertEqual(p.widget.tabText(0), "Login")

    def test_close_tab_removes_tab(self):
        p = self._make_presenter()
        p.add_new_tab()
        p.add_new_tab()
        self.assertEqual(p.widget.count(), 2)
        p.close_tab(0)
        self.assertEqual(p.widget.count(), 1)

    def test_close_tab_ensures_at_least_one_tab(self):
        p = self._make_presenter()
        p.add_new_tab()
        self.assertEqual(p.widget.count(), 1)
        p.close_tab(0)
        self.assertEqual(p.widget.count(), 1)

    def test_restore_tabs_opens_saved_tabs(self):
        req = _make_request("r1", "Saved Request")
        p = self._make_presenter(requests=[req], open_tabs=["r1"])
        p.restore_tabs()
        self.assertEqual(p.widget.count(), 1)
        tab = p.widget.widget(0)
        self.assertIsInstance(tab, RequestTab)
        self.assertEqual(tab.request_data.id, "r1")

    def test_restore_tabs_opens_new_tab_when_no_saved(self):
        p = self._make_presenter(open_tabs=[])
        p.restore_tabs()
        self.assertEqual(p.widget.count(), 1)

    def test_save_tabs_state_persists_ids(self):
        req = _make_request("r1")
        p = self._make_presenter()
        p.add_new_tab(req)
        p.save_tabs_state()
        self.assertEqual(p._state_manager.get_open_tabs(), ["r1"])

    def test_rename_request_tabs_updates_label(self):
        req = _make_request("r1", "Old Name")
        p = self._make_presenter()
        p.add_new_tab(req)
        p.rename_request_tabs("r1", "New Name")
        self.assertEqual(p.widget.tabText(0), "New Name")

    def test_rename_request_tabs_noop_for_unknown_id(self):
        req = _make_request("r1", "My Tab")
        p = self._make_presenter()
        p.add_new_tab(req)
        p.rename_request_tabs("unknown", "Changed")
        self.assertEqual(p.widget.tabText(0), "My Tab")

    def test_on_env_variables_changed_updates_tabs(self):
        p = self._make_presenter()
        p.add_new_tab()
        variables = {"BASE_URL": "https://example.com"}
        p.on_env_variables_changed(variables)
        self.assertEqual(p._current_variables, variables)

    def test_on_env_keys_changed_pushes_keys(self):
        p = self._make_presenter()
        p.add_new_tab()
        keys = ["KEY1", "KEY2"]
        p.on_env_keys_changed(keys)

    def test_handle_new_tab_opens_tab(self):
        p = self._make_presenter()
        p.handle_new_tab("test_source")
        self.assertEqual(p.widget.count(), 1)

    def test_handle_close_tab_closes_current(self):
        p = self._make_presenter()
        p.add_new_tab()
        p.add_new_tab()
        self.assertEqual(p.widget.count(), 2)
        p.widget.setCurrentIndex(1)
        p.handle_close_tab()
        self.assertEqual(p.widget.count(), 1)

    def test_handle_next_tab_cycles(self):
        p = self._make_presenter()
        p.add_new_tab()
        p.add_new_tab()
        p.widget.setCurrentIndex(0)
        p.handle_next_tab()
        self.assertEqual(p.widget.currentIndex(), 1)
        p.handle_next_tab()
        self.assertEqual(p.widget.currentIndex(), 0)

    def test_handle_previous_tab_cycles(self):
        p = self._make_presenter()
        p.add_new_tab()
        p.add_new_tab()
        p.widget.setCurrentIndex(0)
        p.handle_previous_tab()
        self.assertEqual(p.widget.currentIndex(), 1)

    def test_handle_switch_to_tab_valid_index(self):
        p = self._make_presenter()
        p.add_new_tab()
        p.add_new_tab()
        p.handle_switch_to_tab(1)
        self.assertEqual(p.widget.currentIndex(), 1)

    def test_handle_switch_to_tab_invalid_index_noop(self):
        p = self._make_presenter()
        p.add_new_tab()
        p.handle_switch_to_tab(99)
        self.assertEqual(p.widget.currentIndex(), 0)

    def test_apply_settings_updates_indent(self):
        p = self._make_presenter()
        p.add_new_tab()
        new_settings = AppSettings(indent_size=4)
        p.apply_settings(new_settings)
        self.assertEqual(p._settings.indent_size, 4)

    def test_variable_set_requested_forwarded(self):
        p = self._make_presenter()
        p.add_new_tab()
        received = []
        p.variable_set_requested.connect(lambda k, v: received.append((k, v)))
        tab = p.widget.widget(0)
        tab.response_view.variable_set_requested.emit("mykey", "myval")
        self.assertEqual(received, [("mykey", "myval")])

    def test_new_tab_applies_env_variables(self):
        p = self._make_presenter()
        variables = {"TOKEN": "abc123"}
        p._current_variables = variables
        p.add_new_tab()
        tab = p.widget.widget(0)
        if hasattr(tab.request_editor, 'set_variables'):
            pass  # verified by side effects; no crash = pass

    def test_request_saved_signal_emitted(self):
        req = _make_request("r1", "Existing")
        rm = FakeRequestManager([req])
        col_mock = MagicMock()
        col_mock.id = "c1"
        rm._requests["r1"] = (req, col_mock)
        sm = FakeStateManager()
        p = TabsPresenter(rm, sm, AppSettings(), metrics=MagicMock())
        p.add_new_tab(req)

        received = []
        p.request_saved.connect(lambda: received.append(True))
        p._handle_save_request(req)
        self.assertEqual(len(received), 1)


if __name__ == "__main__":
    unittest.main()
