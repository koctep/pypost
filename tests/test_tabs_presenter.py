import pytest

pytestmark = pytest.mark.timeout(60)

import unittest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QTabBar, QWidget

from pypost.core.request_persisted_fields import (
    persisted_fields_equal,
    snapshot_persisted_fields,
)
from pypost.ui.hotkeys import register_hotkey
from pypost.ui.presenters.tab_dirty import is_tab_dirty
from pypost.ui.presenters.tabs_presenter import TabsPresenter, RequestTab, PLUS_TAB_MARKER
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


def _request_tab_count(presenter: TabsPresenter) -> int:
    return sum(
        1
        for i in range(presenter.widget.count())
        if isinstance(presenter.widget.widget(i), RequestTab)
    )


def _plus_tab_index(presenter: TabsPresenter) -> int:
    tab_bar = presenter.widget.tabBar()
    for i in range(tab_bar.count()):
        if tab_bar.tabData(i) == PLUS_TAB_MARKER:
            return i
    return -1


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
        self.assertEqual(_request_tab_count(p), 1)
        self.assertEqual(p.widget.tabText(0), "New Request")

    def test_add_new_tab_with_request_data(self):
        req = _make_request(name="Login")
        p = self._make_presenter()
        p.add_new_tab(req)
        self.assertEqual(_request_tab_count(p), 1)
        self.assertEqual(p.widget.tabText(0), "Login")

    def test_add_new_tab_deep_copies_request_data(self):
        req = _make_request("r1", "Shared")
        p = self._make_presenter()
        p.add_new_tab(req, save_state=False)
        p.add_new_tab(req, save_state=False)
        tab_a = p.widget.widget(0)
        tab_b = p.widget.widget(1)
        self.assertIsNot(tab_a.request_data, req)
        self.assertIsNot(tab_b.request_data, req)
        self.assertIsNot(tab_a.request_data, tab_b.request_data)
        tab_a.request_editor.url_input.setText("https://tab-a.example.com")
        self.assertNotEqual(
            tab_b.request_editor.url_input.text(),
            "https://tab-a.example.com",
        )

    def test_close_tab_removes_tab(self):
        p = self._make_presenter()
        p.add_new_tab()
        p.add_new_tab()
        self.assertEqual(_request_tab_count(p), 2)
        p.close_tab(0)
        self.assertEqual(_request_tab_count(p), 1)

    def test_close_tab_ensures_at_least_one_tab(self):
        p = self._make_presenter()
        p.add_new_tab()
        self.assertEqual(_request_tab_count(p), 1)
        p.close_tab(0)
        self.assertEqual(_request_tab_count(p), 1)

    def test_close_tabs_for_request_ids_closes_matching_tabs(self):
        req1 = _make_request("r1", "Tab1")
        req2 = _make_request("r2", "Tab2")
        p = self._make_presenter()
        p.add_new_tab(req1, save_state=False)
        p.add_new_tab(req2, save_state=False)
        p.close_tabs_for_request_ids(["r1"])
        self.assertEqual(_request_tab_count(p), 1)
        self.assertEqual(p.widget.widget(0).request_data.id, "r2")

    def test_close_tabs_for_request_ids_keeps_blank_tab_when_all_closed(self):
        req = _make_request("r1", "Only")
        p = self._make_presenter()
        p.add_new_tab(req, save_state=False)
        p.close_tabs_for_request_ids(["r1"])
        self.assertEqual(_request_tab_count(p), 1)
        current = p.widget.currentIndex()
        self.assertNotEqual(current, _plus_tab_index(p))
        self.assertIsInstance(p.widget.widget(current), RequestTab)
        self.assertEqual(p.widget.tabText(current), "New Request")

    def test_close_tabs_for_request_ids_noop_for_empty_list(self):
        req = _make_request("r1", "Open")
        p = self._make_presenter()
        p.add_new_tab(req, save_state=False)
        p.close_tabs_for_request_ids([])
        self.assertEqual(_request_tab_count(p), 1)
        self.assertEqual(p.widget.widget(0).request_data.id, "r1")

    def test_close_tabs_for_request_ids_closes_duplicate_request_tabs(self):
        req = _make_request("r1", "Duplicate")
        p = self._make_presenter()
        p.add_new_tab(req.model_copy(deep=True), save_state=False)
        p.add_new_tab(req.model_copy(deep=True), save_state=False)
        p.add_new_tab(_make_request("r2", "Other"), save_state=False)
        p.close_tabs_for_request_ids(["r1"])
        self.assertEqual(_request_tab_count(p), 1)
        self.assertEqual(p.widget.widget(0).request_data.id, "r2")

    def test_close_tabs_for_request_ids_updates_persisted_state(self):
        req = _make_request("r1", "Tracked")
        p = self._make_presenter()
        p.add_new_tab(req, save_state=True)
        self.assertEqual(p._state_manager.get_open_tabs(), ["r1"])
        p.close_tabs_for_request_ids(["r1"])
        self.assertEqual(p._state_manager.get_open_tabs(), [])

    def test_close_tabs_for_request_ids_rightmost_does_not_land_on_plus(self):
        """PYPOST-831: bulk-closing the rightmost request tab must not select +.

        Qt removeTab can advance current onto the trailing + placeholder when the
        closed set includes the request tab adjacent to +. Production must
        reselect a remaining RequestTab (same rule as single close_tab).
        """
        req1 = _make_request("r1", "Left")
        req2 = _make_request("r2", "Right")
        p = self._make_presenter()
        p.add_new_tab(req1, save_state=False)
        p.add_new_tab(req2, save_state=False)
        self.assertEqual(_request_tab_count(p), 2)
        p.widget.setCurrentIndex(1)
        self.assertEqual(p.widget.currentIndex() + 1, _plus_tab_index(p))
        p.close_tabs_for_request_ids(["r2"])
        self.assertEqual(_request_tab_count(p), 1)
        current = p.widget.currentIndex()
        plus_idx = _plus_tab_index(p)
        self.assertNotEqual(current, plus_idx)
        self.assertIsInstance(p.widget.widget(current), RequestTab)
        self.assertEqual(p.widget.widget(current).request_data.id, "r1")

    def test_close_tabs_for_request_ids_multiple_rightmost_does_not_land_on_plus(
        self,
    ):
        """PYPOST-831: bulk-closing several rightmost request tabs must not select +."""
        req1 = _make_request("r1", "Keep")
        req2 = _make_request("r2", "CloseA")
        req3 = _make_request("r3", "CloseB")
        p = self._make_presenter()
        p.add_new_tab(req1, save_state=False)
        p.add_new_tab(req2, save_state=False)
        p.add_new_tab(req3, save_state=False)
        self.assertEqual(_request_tab_count(p), 3)
        p.widget.setCurrentIndex(2)
        self.assertEqual(p.widget.currentIndex() + 1, _plus_tab_index(p))
        p.close_tabs_for_request_ids(["r2", "r3"])
        self.assertEqual(_request_tab_count(p), 1)
        current = p.widget.currentIndex()
        plus_idx = _plus_tab_index(p)
        self.assertNotEqual(current, plus_idx)
        self.assertIsInstance(p.widget.widget(current), RequestTab)
        self.assertEqual(p.widget.widget(current).request_data.id, "r1")

    def test_restore_tabs_opens_saved_tabs(self):
        req = _make_request("r1", "Saved Request")
        p = self._make_presenter(requests=[req], open_tabs=["r1"])
        p.restore_tabs()
        self.assertEqual(_request_tab_count(p), 1)
        tab = p.widget.widget(0)
        self.assertIsInstance(tab, RequestTab)
        self.assertEqual(tab.request_data.id, "r1")

    def test_restore_tabs_opens_new_tab_when_no_saved(self):
        p = self._make_presenter(open_tabs=[])
        p.restore_tabs()
        self.assertEqual(_request_tab_count(p), 1)

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
        tab = p.widget.widget(0)
        variables = {"BASE_URL": "https://example.com"}
        p.on_env_variables_changed(variables)
        self.assertEqual(p._current_variables, variables)
        self.assertEqual(tab.request_editor.url_input._variables, variables)

    def test_on_env_keys_changed_pushes_keys(self):
        p = self._make_presenter()
        p.add_new_tab()
        keys = ["KEY1", "KEY2"]
        p.on_env_keys_changed(keys)

    def test_on_env_hidden_keys_changed_pushes_to_request_editor(self):
        p = self._make_presenter()
        p.add_new_tab()
        tab = p.widget.widget(0)
        tab.request_editor.set_hidden_keys = MagicMock()
        hidden_keys = {"TOKEN"}
        p.on_env_hidden_keys_changed(hidden_keys)
        tab.request_editor.set_hidden_keys.assert_called_once_with(hidden_keys)

    def test_handle_new_tab_opens_tab(self):
        p = self._make_presenter()
        p.handle_new_tab("test_source")
        self.assertEqual(_request_tab_count(p), 1)

    def test_plus_tab_is_last(self):
        p = self._make_presenter()
        p.add_new_tab()
        p.add_new_tab()
        plus_idx = _plus_tab_index(p)
        self.assertGreaterEqual(plus_idx, 0)
        self.assertEqual(plus_idx, p.widget.count() - 1)

    def test_plus_tab_click_adds_request_tab(self):
        p = self._make_presenter()
        p.add_new_tab()
        before = _request_tab_count(p)
        plus_idx = _plus_tab_index(p)
        tab_bar = p.widget.tabBar()
        plus_btn = tab_bar.tabButton(plus_idx, QTabBar.ButtonPosition.LeftSide)
        QTest.mouseClick(plus_btn, Qt.MouseButton.LeftButton)
        self.assertEqual(_request_tab_count(p), before + 1)
        self.assertEqual(_plus_tab_index(p), p.widget.count() - 1)

    def test_plus_tab_tab_bar_clicked_adds_request_tab(self):
        """Fallback path: tabBarClicked on plus index adds a request tab."""
        p = self._make_presenter()
        p.add_new_tab()
        before = _request_tab_count(p)
        plus_idx = _plus_tab_index(p)
        tab_bar = p.widget.tabBar()
        tab_bar.tabBarClicked.emit(plus_idx)
        self.assertEqual(_request_tab_count(p), before + 1)
        self.assertEqual(_plus_tab_index(p), p.widget.count() - 1)

    def test_plus_tab_close_is_ignored(self):
        p = self._make_presenter()
        p.add_new_tab()
        plus_idx = _plus_tab_index(p)
        p.close_tab(plus_idx)
        self.assertEqual(_plus_tab_index(p), plus_idx)
        self.assertEqual(_request_tab_count(p), 1)

    def test_close_first_of_two_tabs_focuses_remaining_request_tab(self):
        """PYPOST-818: after closing first of two tabs, focus stays on request, not +."""
        p = self._make_presenter()
        p.add_new_tab()
        p.add_new_tab()
        self.assertEqual(_request_tab_count(p), 2)
        p.widget.setCurrentIndex(0)
        p.close_tab(0)
        self.assertEqual(_request_tab_count(p), 1)
        current = p.widget.currentIndex()
        plus_idx = _plus_tab_index(p)
        self.assertNotEqual(current, plus_idx)
        self.assertIsInstance(p.widget.widget(current), RequestTab)

    def test_close_rightmost_of_two_tabs_does_not_land_on_plus(self):
        """PYPOST-818: closing the request tab next to + must not select +.

        This is the common app path (close current / rightmost request tab).
        Qt removeTab advances current to the next index, which is the trailing
        + placeholder — production must reselect a remaining RequestTab.
        """
        p = self._make_presenter()
        p.add_new_tab()
        p.add_new_tab()
        self.assertEqual(_request_tab_count(p), 2)
        p.widget.setCurrentIndex(1)
        self.assertEqual(p.widget.currentIndex() + 1, _plus_tab_index(p))
        p.close_tab(1)
        self.assertEqual(_request_tab_count(p), 1)
        current = p.widget.currentIndex()
        plus_idx = _plus_tab_index(p)
        self.assertNotEqual(current, plus_idx)
        self.assertIsInstance(p.widget.widget(current), RequestTab)

    def test_close_middle_of_three_tabs_focuses_remaining_request_tab(self):
        """PYPOST-820: after closing middle of three tabs, focus stays on request, not +."""
        p = self._make_presenter()
        p.add_new_tab()
        p.add_new_tab()
        p.add_new_tab()
        self.assertEqual(_request_tab_count(p), 3)
        p.widget.setCurrentIndex(1)
        p.close_tab(1)
        self.assertEqual(_request_tab_count(p), 2)
        current = p.widget.currentIndex()
        plus_idx = _plus_tab_index(p)
        self.assertNotEqual(current, plus_idx)
        self.assertIsInstance(p.widget.widget(current), RequestTab)

    def test_close_rightmost_of_three_tabs_does_not_land_on_plus(self):
        """PYPOST-820: closing last request tab (adjacent to +) must not select +."""
        p = self._make_presenter()
        p.add_new_tab()
        p.add_new_tab()
        p.add_new_tab()
        self.assertEqual(_request_tab_count(p), 3)
        p.widget.setCurrentIndex(2)
        self.assertEqual(p.widget.currentIndex() + 1, _plus_tab_index(p))
        p.close_tab(2)
        self.assertEqual(_request_tab_count(p), 2)
        current = p.widget.currentIndex()
        plus_idx = _plus_tab_index(p)
        self.assertNotEqual(current, plus_idx)
        self.assertIsInstance(p.widget.widget(current), RequestTab)

    def test_close_last_request_tab_focuses_replacement_not_plus(self):
        """PYPOST-819: closing the last request tab focuses a replacement, not +.

        Product expectation: close_tab replaces the last closed request tab via
        add_new_tab (blank "New Request") and selects that RequestTab. Focus must
        never stick on the trailing + control as the only active tab without a
        request workspace.
        """
        p = self._make_presenter()
        p.add_new_tab()
        self.assertEqual(_request_tab_count(p), 1)
        p.close_tab(0)
        self.assertEqual(_request_tab_count(p), 1)
        current = p.widget.currentIndex()
        plus_idx = _plus_tab_index(p)
        self.assertNotEqual(current, plus_idx)
        self.assertIsInstance(p.widget.widget(current), RequestTab)
        self.assertEqual(p.widget.tabText(current), "New Request")

    def test_handle_close_tab_closes_current(self):
        p = self._make_presenter()
        p.add_new_tab()
        p.add_new_tab()
        self.assertEqual(_request_tab_count(p), 2)
        p.widget.setCurrentIndex(1)
        p.handle_close_tab()
        self.assertEqual(_request_tab_count(p), 1)
        current = p.widget.currentIndex()
        self.assertNotEqual(current, _plus_tab_index(p))
        self.assertIsInstance(p.widget.widget(current), RequestTab)

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

    def test_next_previous_tab_hotkeys_keep_focus_on_request_tabs(self):
        """PYPOST-822: next/previous tab hotkeys move focus among request tabs, not +.

        Product map (MainWindow._setup_shortcuts): Next Tab Ctrl+Tab →
        handle_next_tab; Previous Tab Ctrl+Shift+Tab → handle_previous_tab.
        QShortcut / synthetic key delivery is flaky under QT_QPA_PLATFORM=offscreen
        (no reliable activated window for shortcut context), so this test registers
        the same hotkey map via register_hotkey and activates the tagged QActions
        with triggered.emit — closest product path that still validates map wiring.
        """
        p = self._make_presenter()
        p.add_new_tab()
        p.add_new_tab()
        self.assertEqual(_request_tab_count(p), 2)
        plus_idx = _plus_tab_index(p)
        self.assertEqual(plus_idx, p.widget.count() - 1)

        host = QWidget()
        try:
            register_hotkey(
                host,
                section="Tabs",
                label="Next Tab",
                keys=("Ctrl+Tab",),
                slot=p.handle_next_tab,
                order=3,
            )
            register_hotkey(
                host,
                section="Tabs",
                label="Previous Tab",
                keys=("Ctrl+Shift+Tab",),
                slot=p.handle_previous_tab,
                order=4,
            )

            actions_by_label = {
                action.text(): action
                for action in host.findChildren(QAction)
                if action.text() in ("Next Tab", "Previous Tab")
            }
            self.assertIn("Next Tab", actions_by_label)
            self.assertIn("Previous Tab", actions_by_label)
            next_action = actions_by_label["Next Tab"]
            prev_action = actions_by_label["Previous Tab"]
            portable = QKeySequence.SequenceFormat.PortableText
            self.assertEqual(next_action.shortcut().toString(portable), "Ctrl+Tab")
            self.assertEqual(prev_action.shortcut().toString(portable), "Ctrl+Shift+Tab")

            def _assert_focus_on_request_tab() -> int:
                current = p.widget.currentIndex()
                self.assertNotEqual(current, _plus_tab_index(p))
                self.assertIsInstance(p.widget.widget(current), RequestTab)
                return current

            p.widget.setCurrentIndex(0)
            next_action.triggered.emit()
            self.assertEqual(_assert_focus_on_request_tab(), 1)
            next_action.triggered.emit()
            self.assertEqual(_assert_focus_on_request_tab(), 0)
            prev_action.triggered.emit()
            self.assertEqual(_assert_focus_on_request_tab(), 1)
        finally:
            host.close()

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
        self.assertEqual(tab.request_editor.url_input._variables, variables)

    def test_save_as_emits_request_save_as_completed_not_request_saved(self):
        from pypost.models.models import Collection

        req = _make_request("r1", "Source")
        col = Collection(id="c1", name="API", requests=[req])
        rm = FakeRequestManager([req])
        rm.collections = [col]
        p = TabsPresenter(rm, FakeStateManager(), AppSettings(), metrics=MagicMock())
        p.add_new_tab(req, save_state=False)
        tab = p.widget.widget(0)

        save_as_received = []
        saved_received = []
        p.request_save_as_completed.connect(
            lambda request, collection_id: save_as_received.append((request.id, collection_id))
        )
        p.request_saved.connect(lambda: saved_received.append(True))

        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = True
        mock_dialog.selected_collection_id = "c1"
        mock_dialog.new_collection_name = ""
        mock_dialog.request_name = "Copy"

        with patch(
            "pypost.ui.request_save_orchestrator.SaveRequestDialog",
            return_value=mock_dialog,
        ):
            p._handle_save_as_request(tab, req)

        self.assertEqual(len(save_as_received), 1)
        self.assertNotEqual(save_as_received[0][0], "r1")
        self.assertEqual(save_as_received[0][1], "c1")
        self.assertEqual(len(saved_received), 0)

    def test_save_as_preserves_original_request_id(self):
        from pypost.models.models import Collection

        source = _make_request("r1", "Source")
        source.url = "https://original.example.com"
        col = Collection(id="c1", name="API", requests=[source])
        rm = FakeRequestManager([source])
        rm.collections = [col]
        p = TabsPresenter(rm, FakeStateManager(), AppSettings(), metrics=MagicMock())
        p.add_new_tab(source, save_state=False)

        tab = p.widget.widget(0)
        tab.request_editor.url_input.setText("https://copy.example.com")
        save_as_input = tab.request_editor.get_request_data_from_ui()

        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = True
        mock_dialog.selected_collection_id = "c1"
        mock_dialog.new_collection_name = ""
        mock_dialog.request_name = "Copy"

        with patch(
            "pypost.ui.request_save_orchestrator.SaveRequestDialog",
            return_value=mock_dialog,
        ):
            p._handle_save_as_request(tab, save_as_input)

        original_lookup = rm.find_request("r1")
        self.assertIsNotNone(original_lookup)
        stored_original, _ = original_lookup
        self.assertEqual(stored_original.id, "r1")
        self.assertEqual(stored_original.url, "https://original.example.com")

        self.assertEqual(len(rm.saved), 1)
        saved_request, saved_collection_id = rm.saved[0]
        self.assertNotEqual(saved_request.id, "r1")
        self.assertEqual(saved_request.url, "https://copy.example.com")
        self.assertEqual(saved_collection_id, "c1")

        self.assertEqual(save_as_input.id, "r1")
        self.assertEqual(tab.request_data.id, saved_request.id)
        self.assertEqual(tab.request_editor.request_data.id, saved_request.id)

    def test_request_saved_signal_emitted(self):
        req = _make_request("r1", "Existing")
        rm = FakeRequestManager([req])
        col_mock = MagicMock()
        col_mock.id = "c1"
        rm._requests["r1"] = (req, col_mock)
        sm = FakeStateManager()
        p = TabsPresenter(rm, sm, AppSettings(), metrics=MagicMock())
        p.add_new_tab(req)
        tab = p.widget.widget(0)

        received = []
        p.request_saved.connect(lambda: received.append(True))
        p._handle_save_request(tab, req)
        self.assertEqual(len(received), 1)

    def test_persisted_baseline_initialized_on_add_new_tab(self):
        req = _make_request("r1", "Baseline")
        p = self._make_presenter()
        p.add_new_tab(req, save_state=False)
        tab = p.widget.widget(0)
        self.assertIsNotNone(tab.persisted_baseline)
        self.assertTrue(persisted_fields_equal(tab.persisted_baseline, req))

    def test_rename_request_tabs_updates_baseline_name(self):
        req = _make_request("r1", "Old Name")
        p = self._make_presenter()
        p.add_new_tab(req, save_state=False)
        tab = p.widget.widget(0)
        p.rename_request_tabs("r1", "New Name")
        self.assertEqual(tab.persisted_baseline.name, "New Name")
        self.assertEqual(tab.request_data.name, "New Name")

    def test_save_overwrite_emits_request_persisted(self):
        req = _make_request("r1", "Existing")
        rm = FakeRequestManager([req])
        p = TabsPresenter(rm, FakeStateManager(), AppSettings(), metrics=MagicMock())
        p.add_new_tab(req, save_state=False)
        tab = p.widget.widget(0)
        tab.request_editor.url_input.setText("https://updated.example.com")
        updated = tab.request_editor.get_request_data_from_ui()

        received = []
        p.request_persisted.connect(
            lambda rid, snap, src: received.append((rid, snap.url, src))
        )
        tab.request_editor.save_requested.emit(updated)
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0][0], "r1")
        self.assertEqual(received[0][1], "https://updated.example.com")
        self.assertIs(received[0][2], tab)

    def test_save_overwrite_updates_all_matching_tab_labels(self):
        req = _make_request("r1", "Old Label")
        rm = FakeRequestManager([req])
        p = TabsPresenter(rm, FakeStateManager(), AppSettings(), metrics=MagicMock())
        p.add_new_tab(req.model_copy(deep=True), save_state=False)
        p.add_new_tab(req.model_copy(deep=True), save_state=False)
        tab_a = p.widget.widget(0)
        tab_a.request_data.name = "Renamed"
        updated = tab_a.request_editor.get_request_data_from_ui()
        updated.name = "Renamed"

        with patch(
            "pypost.ui.presenters.tabs_presenter.prompt_clean_sibling_tab_reload",
            return_value=False,
        ), patch(
            "pypost.ui.presenters.tabs_presenter.prompt_dirty_sibling_tab_reload",
            new=MagicMock(),
        ) as mock_dirty_prompt:
            tab_a.request_editor.save_requested.emit(updated)

        mock_dirty_prompt.assert_not_called()
        self.assertEqual(p.widget.tabText(0), "Renamed")
        self.assertEqual(p.widget.tabText(1), "Renamed")

    def test_save_overwrite_notifies_sibling_tab(self):
        req = _make_request("r1", "Shared")
        rm = FakeRequestManager([req])
        p = TabsPresenter(rm, FakeStateManager(), AppSettings(), metrics=MagicMock())
        p.add_new_tab(req.model_copy(deep=True), save_state=False)
        p.add_new_tab(req.model_copy(deep=True), save_state=False)
        tab_a = p.widget.widget(0)
        tab_a.request_editor.url_input.setText("https://saved-elsewhere.example.com")
        updated = tab_a.request_editor.get_request_data_from_ui()

        with patch(
            "pypost.ui.presenters.tabs_presenter.prompt_clean_sibling_tab_reload",
            return_value=False,
        ) as mock_prompt:
            tab_a.request_editor.save_requested.emit(updated)
            mock_prompt.assert_called()

    def test_dirty_sibling_keeps_draft_when_user_chooses_keep(self):
        req = _make_request("r1", "Shared")
        rm = FakeRequestManager([req])
        p = TabsPresenter(rm, FakeStateManager(), AppSettings(), metrics=MagicMock())
        p.add_new_tab(req.model_copy(deep=True), save_state=False)
        p.add_new_tab(req.model_copy(deep=True), save_state=False)
        tab_a = p.widget.widget(0)
        tab_b = p.widget.widget(1)
        tab_b.request_editor.url_input.setText("https://local-draft.example.com")
        tab_a.request_editor.url_input.setText("https://saved-elsewhere.example.com")
        updated = tab_a.request_editor.get_request_data_from_ui()

        with patch(
            "pypost.ui.presenters.tabs_presenter.prompt_dirty_sibling_tab_reload",
            return_value=False,
        ):
            tab_a.request_editor.save_requested.emit(updated)

        self.assertEqual(
            tab_b.request_editor.url_input.text(),
            "https://local-draft.example.com",
        )
        self.assertTrue(tab_b.stale_persisted)

    def test_clean_sibling_loads_latest_when_user_chooses_load(self):
        req = _make_request("r1", "Shared")
        rm = FakeRequestManager([req])
        p = TabsPresenter(rm, FakeStateManager(), AppSettings(), metrics=MagicMock())
        p.add_new_tab(req.model_copy(deep=True), save_state=False)
        p.add_new_tab(req.model_copy(deep=True), save_state=False)
        tab_a = p.widget.widget(0)
        tab_b = p.widget.widget(1)
        tab_a.request_editor.url_input.setText("https://saved-elsewhere.example.com")
        updated = tab_a.request_editor.get_request_data_from_ui()

        with patch(
            "pypost.ui.presenters.tabs_presenter.prompt_clean_sibling_tab_reload",
            return_value=True,
        ):
            tab_a.request_editor.save_requested.emit(updated)

        self.assertEqual(
            tab_b.request_editor.url_input.text(),
            "https://saved-elsewhere.example.com",
        )
        self.assertFalse(tab_b.stale_persisted)


class TestRequestSync(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_snapshot_persisted_fields_deep_copy(self):
        req = _make_request("r1", "Snap")
        req.headers = {"X-Test": "1"}
        snap = snapshot_persisted_fields(req)
        snap.headers["X-Test"] = "2"
        self.assertEqual(req.headers["X-Test"], "1")

    def test_persisted_fields_equal_detects_url_change(self):
        a = _make_request("r1", "A")
        b = a.model_copy(deep=True)
        b.url = "https://different.example.com"
        self.assertFalse(persisted_fields_equal(a, b))

    def test_is_tab_dirty_when_editor_differs_from_baseline(self):
        req = _make_request("r1", "Dirty")
        tab = RequestTab(req)
        tab.persisted_baseline = snapshot_persisted_fields(req)
        tab.request_editor.url_input.setText("https://edited.example.com")
        self.assertTrue(is_tab_dirty(tab))

    def test_request_tab_layout_method_not_shadowed(self):
        tab = RequestTab()
        self.assertNotIn("layout", tab.__dict__)
        self.assertIsNotNone(tab.layout())


class TestTabsPresenterAlertManagerPropagation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _make_presenter_with_alert_manager(self, alert_manager=None):
        rm = FakeRequestManager()
        sm = FakeStateManager()
        settings = AppSettings()
        return TabsPresenter(rm, sm, settings, metrics=MagicMock(), alert_manager=alert_manager)

    def test_alert_manager_passed_to_worker(self):
        from pypost.core.alert_manager import AlertManager
        mock_am = MagicMock(spec=AlertManager)
        p = self._make_presenter_with_alert_manager(alert_manager=mock_am)

        req = _make_request("r1", "Test", "GET")
        p.add_new_tab(req)
        tab = p.widget.widget(0)

        with patch("pypost.ui.presenters.tabs_presenter.RequestWorker") as MockWorker:
            mock_worker_instance = MagicMock()
            mock_worker_instance.isRunning.return_value = False
            MockWorker.return_value = mock_worker_instance

            tab.request_editor.send_requested.emit(req)

            self.assertTrue(MockWorker.called)
            _, kwargs = MockWorker.call_args
            self.assertIs(kwargs.get("alert_manager"), mock_am)

    def test_no_alert_manager_no_exception(self):
        p = self._make_presenter_with_alert_manager(alert_manager=None)

        req = _make_request("r2", "Test2", "GET")
        p.add_new_tab(req)
        tab = p.widget.widget(0)

        with patch("pypost.ui.presenters.tabs_presenter.RequestWorker") as MockWorker:
            mock_worker_instance = MagicMock()
            mock_worker_instance.isRunning.return_value = False
            MockWorker.return_value = mock_worker_instance

            # Should not raise
            tab.request_editor.send_requested.emit(req)

            _, kwargs = MockWorker.call_args
            self.assertIsNone(kwargs.get("alert_manager"))


class TestTabsPresenterSendRequestTabBinding(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_handle_send_request_accepts_explicit_tab_without_sender(self):
        """PYPOST-71: send handler must not rely on QObject.sender()."""
        rm = FakeRequestManager()
        sm = FakeStateManager()
        settings = AppSettings()
        p = TabsPresenter(rm, sm, settings, metrics=MagicMock())

        req1 = _make_request("r1", "Tab1", "GET")
        req2 = _make_request("r2", "Tab2", "POST")
        p.add_new_tab(req1)
        p.add_new_tab(req2)
        tab1 = p.widget.widget(0)
        tab2 = p.widget.widget(1)
        p.widget.setCurrentIndex(0)

        with patch("pypost.ui.presenters.tabs_presenter.RequestWorker") as MockWorker:
            mock_instance = MagicMock()
            mock_instance.isRunning.return_value = False
            MockWorker.return_value = mock_instance

            p._handle_send_request(tab2, req2)

            MockWorker.assert_called_once()
            self.assertIs(tab2.worker, mock_instance)
            self.assertIsNone(tab1.worker)
            mock_instance.start.assert_called_once()


class TestTabsPresenterSaveTabBinding(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _mock_save_dialog(self, *, request_name: str = "Saved Copy"):
        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = True
        mock_dialog.selected_collection_id = "c1"
        mock_dialog.new_collection_name = ""
        mock_dialog.request_name = request_name
        return mock_dialog

    def test_save_new_applies_to_source_tab_when_index_changes_during_dialog(self):
        """PYPOST-72: save-new must not rely on currentIndex() after modal dialog."""
        from pypost.models.models import Collection

        unsaved = _make_request("new-r", "Unsaved")
        other = _make_request("r2", "Other")
        col = Collection(id="c1", name="API", requests=[])
        rm = FakeRequestManager()
        rm.collections = [col]
        p = TabsPresenter(rm, FakeStateManager(), AppSettings(), metrics=MagicMock())
        p.add_new_tab(unsaved, save_state=False)
        p.add_new_tab(other, save_state=False)
        source_tab = p.widget.widget(0)
        other_tab = p.widget.widget(1)
        p.widget.setCurrentIndex(0)

        mock_dialog = self._mock_save_dialog(request_name="Saved Name")

        def exec_switch_tab():
            p.widget.setCurrentIndex(1)
            return True

        mock_dialog.exec.side_effect = exec_switch_tab

        with patch(
            "pypost.ui.request_save_orchestrator.SaveRequestDialog",
            return_value=mock_dialog,
        ):
            p._handle_save_request(source_tab, unsaved)

        self.assertEqual(source_tab.request_data.name, "Saved Name")
        self.assertEqual(other_tab.request_data.name, "Other")
        self.assertIsNotNone(source_tab.persisted_baseline)

    def test_save_as_applies_to_source_tab_when_index_changes_during_dialog(self):
        """PYPOST-72: save-as must not rely on currentIndex() after modal dialog."""
        from pypost.models.models import Collection

        source = _make_request("r1", "Source")
        other = _make_request("r2", "Other")
        col = Collection(id="c1", name="API", requests=[source])
        rm = FakeRequestManager([source])
        rm.collections = [col]
        p = TabsPresenter(rm, FakeStateManager(), AppSettings(), metrics=MagicMock())
        p.add_new_tab(source, save_state=False)
        p.add_new_tab(other, save_state=False)
        source_tab = p.widget.widget(0)
        other_tab = p.widget.widget(1)
        p.widget.setCurrentIndex(0)

        mock_dialog = self._mock_save_dialog(request_name="Copy")

        def exec_switch_tab():
            p.widget.setCurrentIndex(1)
            return True

        mock_dialog.exec.side_effect = exec_switch_tab

        with patch(
            "pypost.ui.request_save_orchestrator.SaveRequestDialog",
            return_value=mock_dialog,
        ):
            p._handle_save_as_request(source_tab, source)

        self.assertNotEqual(source_tab.request_data.id, "r1")
        self.assertEqual(source_tab.request_data.name, "Copy")
        self.assertEqual(other_tab.request_data.name, "Other")

    def test_handle_save_request_accepts_explicit_tab_without_sender(self):
        """PYPOST-162: save handler must not rely on QObject.sender()."""
        from pypost.models.models import Collection

        unsaved = _make_request("new-r", "Unsaved")
        col = Collection(id="c1", name="API", requests=[])
        rm = FakeRequestManager()
        rm.collections = [col]
        p = TabsPresenter(rm, FakeStateManager(), AppSettings(), metrics=MagicMock())
        p.add_new_tab(unsaved, save_state=False)
        source_tab = p.widget.widget(0)

        mock_dialog = self._mock_save_dialog(request_name="Saved Name")
        with patch(
            "pypost.ui.request_save_orchestrator.SaveRequestDialog",
            return_value=mock_dialog,
        ):
            p._handle_save_request(source_tab, unsaved)

        self.assertEqual(source_tab.request_data.name, "Saved Name")
        self.assertIsNotNone(source_tab.persisted_baseline)


class TestTabsPresenterHiddenKeysForwarding(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_hidden_keys_forwarded_to_worker_after_env_hidden_keys_changed(self):
        from pypost.core.template_service import TemplateService
        rm = FakeRequestManager()
        sm = FakeStateManager()
        settings = AppSettings()
        p = TabsPresenter(rm, sm, settings,
                          metrics=MagicMock(),
                          template_service=TemplateService())

        req = _make_request("r1", "Test", "GET")
        p.add_new_tab(req)
        tab = p.widget.widget(0)

        p.on_env_hidden_keys_changed({"token"})

        with patch("pypost.ui.presenters.tabs_presenter.RequestWorker") as MockWorker:
            mock_instance = MagicMock()
            mock_instance.isRunning.return_value = False
            MockWorker.return_value = mock_instance

            tab.request_editor.send_requested.emit(req)

            _, kwargs = MockWorker.call_args
            self.assertEqual(
                {"token"},
                kwargs.get("hidden_keys"),
                "RequestWorker must receive hidden_keys from _current_hidden_keys",
            )


if __name__ == "__main__":
    unittest.main()
