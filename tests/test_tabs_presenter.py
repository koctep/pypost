import logging
import unittest
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QTabBar, QWidget

from pypost.core.request_persisted_fields import (
    persisted_fields_equal,
    snapshot_persisted_fields,
)
from pypost.ui.hotkeys import register_hotkey
from pypost.ui.presenters.tab_dirty import is_tab_dirty
from pypost.ui.presenters.tabs_presenter import (
    PLUS_TAB_MARKER,
    RequestTab,
    TabsPresenter,
    WebSocketTab,
)
from pypost.models.mcp_client import McpClientConnection
from pypost.models.models import RequestData
from pypost.models.settings import AppSettings
from pypost.models.websocket import WebSocketConnection
from pypost.ui.widget_ids import MCP_CLIENT_TAB_PAGE
from pypost.ui.widgets.mcp_client import McpClientTab
from pypost.ui.widgets.new_tab_protocol_picker import (
    NewTabProtocolPicker,
    TabProtocol,
)

pytestmark = pytest.mark.timeout(60)


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
    """Count workspace tabs that keep the strip non-empty (matches production)."""
    return sum(
        1
        for i in range(presenter.widget.count())
        if isinstance(
            presenter.widget.widget(i),
            (RequestTab, WebSocketTab, McpClientTab),
        )
    )

def _plus_tab_index(presenter: TabsPresenter) -> int:
    tab_bar = presenter.widget.tabBar()
    for i in range(tab_bar.count()):
        if tab_bar.tabData(i) == PLUS_TAB_MARKER:
            return i
    return -1

@pytest.mark.usefixtures("qapp")

class TestTabsPresenter(unittest.TestCase):
    def _make_presenter(self, requests=None, open_tabs=None):
        rm = FakeRequestManager(requests)
        sm = FakeStateManager(open_tabs)
        settings = AppSettings()
        return TabsPresenter(
            rm,
            sm,
            settings,
            metrics=MagicMock(),
            protocol_picker=lambda *_a, **_k: TabProtocol.HTTP,
        )

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
        tab = p.widget.widget(0)
        keys = ["KEY1", "KEY2"]
        p.on_env_keys_changed(keys)
        self.assertEqual(tab.response_view.current_env_keys, keys)

    def test_on_env_keys_changed_ignores_invalid_payload(self):
        p = self._make_presenter()
        p.add_new_tab()
        tab = p.widget.widget(0)
        invalid_payload = "sensitive-token-value"

        with self.assertLogs("pypost.ui.presenters.tabs_presenter", level="WARNING") as caplog:
            p.on_env_keys_changed(invalid_payload)

        self.assertIsNone(tab.response_view.current_env_keys)
        self.assertEqual(
            caplog.output,
            [
                "WARNING:pypost.ui.presenters.tabs_presenter:"
                "env_keys_update_ignored reason=invalid_payload_type type=str",
            ],
        )
        self.assertNotIn(invalid_payload, caplog.output[0])

    def test_on_env_hidden_keys_changed_pushes_to_request_editor(self):
        p = self._make_presenter()
        p.add_new_tab()
        tab = p.widget.widget(0)
        tab.request_editor.set_hidden_keys = MagicMock()
        hidden_keys = {"TOKEN"}
        p.on_env_hidden_keys_changed(hidden_keys)
        tab.request_editor.set_hidden_keys.assert_called_once_with(hidden_keys)

    def test_on_env_variables_changed_updates_mcp_client_tab(self):
        p = self._make_presenter()
        tab = p.add_blank_mcp_client_tab()
        variables = {"host": "127.0.0.1:1080"}
        p.on_env_variables_changed(variables)
        self.assertEqual(tab.presenter._env_vars, variables)
        self.assertEqual(tab.url_input._variables, variables)

    def test_on_env_hidden_keys_changed_updates_mcp_client_tab(self):
        p = self._make_presenter()
        tab = p.add_blank_mcp_client_tab()
        hidden_keys = {"token"}
        p.on_env_hidden_keys_changed(hidden_keys)
        self.assertEqual(tab.presenter._hidden_keys, hidden_keys)
        self.assertEqual(tab.url_input._hidden_keys, hidden_keys)

    def test_add_blank_mcp_client_tab_receives_cached_env(self):
        p = self._make_presenter()
        variables = {"host": "example.test"}
        p.on_env_variables_changed(variables)
        tab = p.add_blank_mcp_client_tab()
        self.assertEqual(tab.presenter._env_vars, variables)

    def test_on_script_output_rejects_invalid_error_payload(self):
        p = self._make_presenter()
        p.add_new_tab()
        tab = p.widget.widget(0)

        with self.assertLogs(
            "pypost.ui.presenters.tabs_presenter_worker",
            level="WARNING",
        ) as caplog:
            p._on_script_output(tab, [], {"secret": "must-not-be-forwarded"})

        self.assertEqual(
            caplog.output,
            [
                "WARNING:pypost.ui.presenters.tabs_presenter_worker:"
                "script_output_ignored reason=invalid_error_type type=dict",
            ],
        )
        self.assertNotIn("must-not-be-forwarded", caplog.output[0])

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

    def test_save_overwrite_without_snapshot_is_rejected(self):
        from pypost.ui.request_save_orchestrator import SaveAction, SaveResult

        req = _make_request("r1", "Existing")
        p = self._make_presenter([req])
        p.add_new_tab(req, save_state=False)
        tab = p.widget.widget(0)
        p._save_orchestrator.save_request = MagicMock(
            return_value=SaveResult(SaveAction.OVERWRITE),
        )
        persisted_slot = MagicMock()
        p.request_persisted.connect(persisted_slot)

        with self.assertLogs("pypost.ui.presenters.tabs_presenter", level="ERROR") as caplog:
            p._handle_save_request(tab, req)

        persisted_slot.assert_not_called()
        self.assertIn("reason=missing_snapshot", caplog.output[0])

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

    def test_add_blank_mcp_client_tab_creates_draft(self):
        p = self._make_presenter()
        tab = p.add_blank_mcp_client_tab()
        idx = p.widget.indexOf(tab)
        self.assertIsInstance(tab, McpClientTab)
        self.assertNotIsInstance(tab, RequestTab)
        self.assertNotIsInstance(tab, WebSocketTab)
        self.assertEqual(p.widget.tabText(idx), "New MCP Client")
        self.assertEqual(tab.connection_data.url, "")
        self.assertEqual(
            tab.connection_data.name,
            "New MCP Client",
        )
        self.assertIsInstance(tab.connection_data, McpClientConnection)

    def test_save_tabs_state_omits_unsaved_mcp_client_draft(self):
        p = self._make_presenter()
        tab = p.add_blank_mcp_client_tab()
        draft_id = tab.connection_data.id
        self.assertNotIn(draft_id, p._state_manager.get_open_tabs())
        self.assertIsInstance(tab.connection_data, McpClientConnection)

        restorer = self._make_presenter(open_tabs=[draft_id])
        restorer.restore_tabs()
        for i in range(restorer.widget.count()):
            self.assertNotIsInstance(
                restorer.widget.widget(i),
                McpClientTab,
            )

    def test_close_tab_calls_mcp_client_presenter_teardown(self):
        p = self._make_presenter()
        tab = p.add_blank_mcp_client_tab()
        presenter = tab.presenter
        teardown = MagicMock()
        presenter.teardown = teardown
        idx = p.widget.indexOf(tab)
        p.close_tab(idx)
        teardown.assert_called_once()

    def test_save_tabs_state_omits_unsaved_websocket_draft(self):
        p = self._make_presenter()
        tab = p.add_blank_websocket_tab()
        draft_id = tab.connection_data.id
        self.assertNotIn(draft_id, p._state_manager.get_open_tabs())
        self.assertIsInstance(tab.connection_data, WebSocketConnection)

        restorer = self._make_presenter(open_tabs=[draft_id])
        restorer.restore_tabs()
        saw_http = False
        for i in range(restorer.widget.count()):
            widget = restorer.widget.widget(i)
            self.assertNotIsInstance(widget, WebSocketTab)
            if isinstance(widget, RequestTab):
                saw_http = True
        self.assertTrue(saw_http)

    def test_close_dirty_websocket_draft_prompts_discard_or_keep(self):
        p = self._make_presenter()
        tab = p.add_blank_websocket_tab()
        tab.connection_editor.url_input.setText("ws://example.com/stream")
        idx = p.widget.indexOf(tab)
        presenter = tab.presenter
        teardown = MagicMock()
        presenter.teardown = teardown
        prompt_path = (
            "pypost.ui.presenters.tabs_presenter.prompt_unsaved_draft_tab_close"
        )

        with patch(prompt_path, return_value=False) as prompt:
            p.close_tab(idx)
        prompt.assert_called_once()
        self.assertEqual(p.widget.indexOf(tab), idx)
        teardown.assert_not_called()

        with patch(prompt_path, return_value=True) as prompt:
            p.close_tab(idx)
        prompt.assert_called_once()
        teardown.assert_called_once()
        self.assertEqual(p.widget.indexOf(tab), -1)

    def test_two_blank_websocket_tabs_do_not_merge(self):
        p = self._make_presenter()
        tab_a = p.add_blank_websocket_tab()
        tab_b = p.add_blank_websocket_tab()
        self.assertIsNot(tab_a, tab_b)
        idx_a = p.widget.indexOf(tab_a)
        idx_b = p.widget.indexOf(tab_b)
        self.assertNotEqual(idx_a, idx_b)
        self.assertEqual(p.widget.tabText(idx_a), "New WebSocket")
        self.assertEqual(p.widget.tabText(idx_b), "New WebSocket")
        self.assertEqual(tab_a.connection_editor.url_input.text(), "")
        self.assertEqual(tab_b.connection_editor.url_input.text(), "")

    def test_open_websocket_tab_still_dedups_saved_profile(self):
        p = self._make_presenter()
        conn = WebSocketConnection(id="ws-saved-dedup", name="Saved Feed")
        first = p.open_websocket_tab(conn)
        second = p.open_websocket_tab(conn)
        self.assertIs(first, second)
        ws_tabs = [
            p.widget.widget(i)
            for i in range(p.widget.count())
            if isinstance(p.widget.widget(i), WebSocketTab)
        ]
        self.assertEqual(len(ws_tabs), 1)

    def test_save_tabs_state_still_persists_saved_websocket_id(self):
        from pypost.models.models import Collection

        p = self._make_presenter()
        conn = WebSocketConnection(
            id="ws-saved-persist",
            name="Saved Feed",
            url="wss://example.com/stream",
        )
        p._request_manager.collections.append(
            Collection(name="Streams", websockets=[conn])
        )
        p.open_websocket_tab(conn)
        p.save_tabs_state()
        self.assertIn("ws-saved-persist", p._state_manager.get_open_tabs())

    def test_close_clean_websocket_draft_does_not_prompt(self):
        p = self._make_presenter()
        tab = p.add_blank_websocket_tab()
        idx = p.widget.indexOf(tab)
        presenter = tab.presenter
        teardown = MagicMock()
        presenter.teardown = teardown
        prompt_path = (
            "pypost.ui.presenters.tabs_presenter.prompt_unsaved_draft_tab_close"
        )
        with patch(prompt_path, return_value=False) as prompt:
            p.close_tab(idx)
        prompt.assert_not_called()
        teardown.assert_called_once()
        self.assertEqual(p.widget.indexOf(tab), -1)

    def test_close_saved_websocket_tab_with_edited_url_does_not_prompt(self):
        from pypost.models.models import Collection

        p = self._make_presenter()
        conn = WebSocketConnection(
            id="ws-saved-url-edit",
            name="Saved Feed",
            url="wss://example.com/original",
        )
        p._request_manager.collections.append(
            Collection(name="Streams", websockets=[conn])
        )
        tab = p.open_websocket_tab(conn)
        tab.connection_editor.url_input.setText("wss://example.com/modified")
        idx = p.widget.indexOf(tab)
        presenter = tab.presenter
        teardown = MagicMock()
        presenter.teardown = teardown
        prompt_path = (
            "pypost.ui.presenters.tabs_presenter.prompt_unsaved_draft_tab_close"
        )
        with patch(prompt_path, return_value=False) as prompt:
            p.close_tab(idx)
        prompt.assert_not_called()
        teardown.assert_called_once()
        self.assertEqual(p.widget.indexOf(tab), -1)

    def test_is_websocket_draft_dirty_editor_snapshots(self):
        from pypost.ui.presenters.tab_dirty import is_websocket_draft_dirty

        p = self._make_presenter()
        tab = p.add_blank_websocket_tab()
        self.assertFalse(is_websocket_draft_dirty(tab))

        # URL edit
        tab.connection_editor.url_input.setText("wss://example.com/socket")
        self.assertTrue(is_websocket_draft_dirty(tab))
        tab.connection_editor.url_input.setText("")
        self.assertFalse(is_websocket_draft_dirty(tab))

        # Params table edit
        tab.connection_editor.params_table.set_data({"foo": "bar"})
        self.assertTrue(is_websocket_draft_dirty(tab))
        tab.connection_editor.params_table.set_data({})
        self.assertFalse(is_websocket_draft_dirty(tab))

        # Headers table edit
        tab.connection_editor.headers_table.set_data({"Authorization": "Bearer token"})
        self.assertTrue(is_websocket_draft_dirty(tab))
        tab.connection_editor.headers_table.set_data({})
        self.assertFalse(is_websocket_draft_dirty(tab))

        # Subprotocols edit
        tab.connection_editor.subprotocols_input.setText("graphql-ws, json")
        self.assertTrue(is_websocket_draft_dirty(tab))
        tab.connection_editor.subprotocols_input.setText("")
        self.assertFalse(is_websocket_draft_dirty(tab))

        # MCP Expose checkbox edit
        tab.connection_editor.mcp_expose_check.setChecked(True)
        self.assertTrue(is_websocket_draft_dirty(tab))
        tab.connection_editor.mcp_expose_check.setChecked(False)
        self.assertFalse(is_websocket_draft_dirty(tab))

        # MCP Description edit
        tab.connection_editor.mcp_description_edit.setText("MCP description")
        self.assertTrue(is_websocket_draft_dirty(tab))
        tab.connection_editor.mcp_description_edit.setText("")
        self.assertFalse(is_websocket_draft_dirty(tab))

    def test_save_tabs_state_mixed_saved_and_draft_websocket_tabs(self):
        from pypost.models.models import Collection

        p = self._make_presenter()
        conn = WebSocketConnection(
            id="ws-saved-mixed",
            name="Saved Mixed Feed",
            url="wss://example.com/live",
        )
        p._request_manager.collections.append(
            Collection(name="Streams", websockets=[conn])
        )
        p.open_websocket_tab(conn)
        draft_tab = p.add_blank_websocket_tab()

        p.save_tabs_state()
        open_tabs = p._state_manager.get_open_tabs()
        self.assertIn("ws-saved-mixed", open_tabs)
        self.assertNotIn(draft_tab.connection_data.id, open_tabs)

    def test_close_dirty_http_draft_prompts_discard_or_keep(self):
        p = self._make_presenter()
        p.add_new_tab()
        tab = p.widget.widget(0)
        tab.request_editor.url_input.setText("https://example.com/api/test")
        prompt_path = (
            "pypost.ui.presenters.tabs_presenter.prompt_unsaved_draft_tab_close"
        )

        with patch(prompt_path, return_value=False) as prompt:
            p.close_tab(0)
        prompt.assert_called_once()
        self.assertEqual(p.widget.indexOf(tab), 0)

        with patch(prompt_path, return_value=True) as prompt:
            p.close_tab(0)
        prompt.assert_called_once()
        self.assertEqual(p.widget.indexOf(tab), -1)

    def test_close_clean_http_draft_does_not_prompt(self):
        p = self._make_presenter()
        p.add_new_tab()
        tab = p.widget.widget(0)
        prompt_path = (
            "pypost.ui.presenters.tabs_presenter.prompt_unsaved_draft_tab_close"
        )
        with patch(prompt_path, return_value=False) as prompt:
            p.close_tab(0)
        prompt.assert_not_called()
        self.assertEqual(p.widget.indexOf(tab), -1)

    def test_is_request_draft_dirty_editor_snapshots(self):
        from pypost.ui.presenters.tab_dirty import is_request_draft_dirty

        p = self._make_presenter()
        p.add_new_tab()
        tab = p.widget.widget(0)
        self.assertFalse(is_request_draft_dirty(tab))

        # URL edit
        tab.request_editor.url_input.setText("https://example.com")
        self.assertTrue(is_request_draft_dirty(tab))
        tab.request_editor.url_input.setText("")
        self.assertFalse(is_request_draft_dirty(tab))

        # Method edit
        tab.request_editor.method_combo.setCurrentText("POST")
        self.assertTrue(is_request_draft_dirty(tab))
        tab.request_editor.method_combo.setCurrentText("GET")
        self.assertFalse(is_request_draft_dirty(tab))

        # Body edit
        tab.request_editor.body_edit.setPlainText("{\"hello\": \"world\"}")
        self.assertTrue(is_request_draft_dirty(tab))
        tab.request_editor.body_edit.setPlainText("")
        self.assertFalse(is_request_draft_dirty(tab))

        # Params table edit
        tab.request_editor.params_table.set_data({"q": "search"})
        self.assertTrue(is_request_draft_dirty(tab))
        tab.request_editor.params_table.set_data({})
        self.assertFalse(is_request_draft_dirty(tab))

        # Headers table edit
        tab.request_editor.headers_table.set_data({"Accept": "application/json"})
        self.assertTrue(is_request_draft_dirty(tab))
        tab.request_editor.headers_table.set_data({})
        self.assertFalse(is_request_draft_dirty(tab))

        # MCP check edit
        tab.request_editor.mcp_check.setChecked(True)
        self.assertTrue(is_request_draft_dirty(tab))
        tab.request_editor.mcp_check.setChecked(False)
        self.assertFalse(is_request_draft_dirty(tab))

    def test_save_tabs_state_constructs_websocket_registry_once(self):
        from pypost.core.websocket_registry import WebSocketRegistry

        p = self._make_presenter()
        p.add_blank_websocket_tab(save_state=False)
        p.add_blank_websocket_tab(save_state=False)
        p.add_blank_websocket_tab(save_state=False)

        with patch.object(
            WebSocketRegistry, "__init__", return_value=None
        ) as mock_init, patch.object(
            WebSocketRegistry, "find_websocket", return_value=None
        ):
            p.save_tabs_state()
            self.assertEqual(mock_init.call_count, 1)

    def test_close_tab_constructs_websocket_registry_once(self):
        from pypost.core.websocket_registry import WebSocketRegistry

        p = self._make_presenter()
        tab1 = p.add_blank_websocket_tab(save_state=False)
        p.add_blank_websocket_tab(save_state=False)
        idx = p.widget.indexOf(tab1)

        with patch.object(
            WebSocketRegistry, "__init__", return_value=None
        ) as mock_init, patch.object(
            WebSocketRegistry, "find_websocket", return_value=None
        ):
            p.close_tab(idx)
            # Exactly 1 in close_workspace_tab check + 1 in save_tabs_state after tab removal
            self.assertEqual(mock_init.call_count, 2)


_DRAFT_LOGGER = "pypost.ui.presenters.tabs_presenter_draft"


@pytest.mark.usefixtures("qapp")
class TestWebsocketDraftObservability:
    def _make_presenter(self):
        return TabsPresenter(
            FakeRequestManager(),
            FakeStateManager(),
            AppSettings(),
            metrics=MagicMock(),
            protocol_picker=lambda *_a, **_k: TabProtocol.HTTP,
        )

    def test_save_tabs_state_logs_omitted_websocket_draft_id(self, caplog):
        p = self._make_presenter()
        with caplog.at_level(logging.INFO, logger=_DRAFT_LOGGER):
            tab = p.add_blank_websocket_tab()
        draft_id = tab.connection_data.id
        messages = [r.message for r in caplog.records]
        omit = f"websocket_draft_omitted_from_open_tabs connection_id={draft_id}"
        assert omit in messages
        assert any(
            "open_tabs_filter omitted_draft_count=1" in m
            and "persisted_ws_count=0" in m
            and "persisted_mcp_count=0" in m
            for m in messages
        )
        assert not any("url=" in m for m in messages)
        assert not any("headers=" in m for m in messages)

    def test_save_tabs_state_logs_persisted_saved_websocket_id(self, caplog):
        from pypost.models.models import Collection

        p = self._make_presenter()
        conn = WebSocketConnection(
            id="ws-saved-persist-log",
            name="Saved Feed",
            url="wss://example.com/stream",
        )
        p._request_manager.collections.append(
            Collection(name="Streams", websockets=[conn])
        )
        p.open_websocket_tab(conn, save_state=False)
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=_DRAFT_LOGGER):
            p.save_tabs_state()
        messages = [r.message for r in caplog.records]
        persist = (
            "websocket_saved_tab_persisted_in_open_tabs "
            "connection_id=ws-saved-persist-log"
        )
        assert persist in messages
        assert any(
            "open_tabs_filter omitted_draft_count=0" in m
            and "persisted_ws_count=1" in m
            and "persisted_mcp_count=0" in m
            for m in messages
        )
        assert not any("url=" in m for m in messages)
        assert not any("wss://example.com" in m for m in messages)

    def test_close_dirty_websocket_draft_logs_keep_and_discard(self, caplog):
        p = self._make_presenter()
        tab = p.add_blank_websocket_tab()
        tab.connection_editor.url_input.setText("ws://example.com/stream")
        idx = p.widget.indexOf(tab)
        draft_id = tab.connection_data.id
        prompt_path = (
            "pypost.ui.presenters.tabs_presenter.prompt_unsaved_draft_tab_close"
        )
        with caplog.at_level(logging.INFO, logger=_DRAFT_LOGGER):
            with patch(prompt_path, return_value=False):
                p.close_tab(idx)
        keep = (
            f"websocket_draft_dirty_close_prompt connection_id={draft_id} "
            "choice=keep"
        )
        assert keep in [r.message for r in caplog.records]
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=_DRAFT_LOGGER):
            with patch(prompt_path, return_value=True):
                p.close_tab(idx)
        messages = [r.message for r in caplog.records]
        discard = (
            f"websocket_draft_dirty_close_prompt connection_id={draft_id} "
            "choice=discard"
        )
        assert discard in messages
        assert not any("url=" in m for m in messages)
        assert not any("ws://example.com" in m for m in messages)

    def test_close_clean_websocket_draft_logs_without_prompt(self, caplog):
        p = self._make_presenter()
        tab = p.add_blank_websocket_tab()
        idx = p.widget.indexOf(tab)
        draft_id = tab.connection_data.id
        prompt_path = (
            "pypost.ui.presenters.tabs_presenter.prompt_unsaved_draft_tab_close"
        )
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=_DRAFT_LOGGER):
            with patch(prompt_path, return_value=False) as prompt:
                p.close_tab(idx)
        prompt.assert_not_called()
        messages = [r.message for r in caplog.records]
        clean = f"websocket_draft_clean_close connection_id={draft_id}"
        assert clean in messages
        assert not any("websocket_draft_dirty_close_prompt" in m for m in messages)
        assert not any("url=" in m for m in messages)

    def test_close_dirty_http_draft_logs_keep_and_discard(self, caplog):
        p = self._make_presenter()
        p.add_new_tab()
        tab = p.widget.widget(0)
        tab.request_editor.url_input.setText("https://example.com/api")
        req_id = tab.request_editor.request_data.id
        prompt_path = (
            "pypost.ui.presenters.tabs_presenter.prompt_unsaved_draft_tab_close"
        )
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=_DRAFT_LOGGER):
            with patch(prompt_path, return_value=False):
                p.close_tab(0)
        keep = (
            f"request_draft_dirty_close_prompt request_id={req_id} "
            "choice=keep"
        )
        assert keep in [r.message for r in caplog.records]
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=_DRAFT_LOGGER):
            with patch(prompt_path, return_value=True):
                p.close_tab(0)
        messages = [r.message for r in caplog.records]
        discard = (
            f"request_draft_dirty_close_prompt request_id={req_id} "
            "choice=discard"
        )
        assert discard in messages
        assert not any("url=" in m for m in messages)
        assert not any("https://example.com" in m for m in messages)

    def test_close_clean_http_draft_logs_without_prompt(self, caplog):
        p = self._make_presenter()
        p.add_new_tab()
        tab = p.widget.widget(0)
        req_id = tab.request_editor.request_data.id
        prompt_path = (
            "pypost.ui.presenters.tabs_presenter.prompt_unsaved_draft_tab_close"
        )
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=_DRAFT_LOGGER):
            with patch(prompt_path, return_value=False) as prompt:
                p.close_tab(0)
        prompt.assert_not_called()
        messages = [r.message for r in caplog.records]
        clean = f"request_draft_clean_close request_id={req_id}"
        assert clean in messages
        assert not any("request_draft_dirty_close_prompt" in m for m in messages)
        assert not any("url=" in m for m in messages)


@pytest.mark.usefixtures("qapp")

class TestRequestSync(unittest.TestCase):
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

@pytest.mark.usefixtures("qapp")

class TestTabsPresenterAlertManagerPropagation(unittest.TestCase):
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

@pytest.mark.usefixtures("qapp")

class TestTabsPresenterSendRequestTabBinding(unittest.TestCase):
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

@pytest.mark.usefixtures("qapp")

class TestTabsPresenterSaveTabBinding(unittest.TestCase):
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

@pytest.mark.usefixtures("qapp")

class TestTabsPresenterHiddenKeysForwarding(unittest.TestCase):
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


@pytest.mark.usefixtures("qapp")
class TestHandleNewTabProtocolPicker(unittest.TestCase):
    """PYPOST-1157: picker before editor; HTTP default; cancel is a no-op."""

    def _make_presenter(self, protocol_picker=None):
        return TabsPresenter(
            FakeRequestManager(),
            FakeStateManager(),
            AppSettings(),
            metrics=MagicMock(),
            protocol_picker=protocol_picker,
        )

    def _editor_tabs(self, presenter):
        tabs = []
        for i in range(presenter.widget.count()):
            widget = presenter.widget.widget(i)
            if isinstance(widget, (RequestTab, WebSocketTab)):
                tabs.append(widget)
        return tabs

    def _assert_new_tab_metric(self, mock_track, source, protocol):
        mock_track.assert_called()
        args, kwargs = mock_track.call_args
        got_source = args[0] if args else kwargs.get("source")
        if len(args) > 1:
            got_protocol = args[1]
        else:
            got_protocol = kwargs.get("protocol")
        self.assertEqual(got_source, source)
        self.assertEqual(got_protocol, protocol)

    def test_handle_new_tab_shows_protocol_picker(self):
        order = []

        def picker(*_args, **_kwargs):
            order.append("picker")
            return TabProtocol.HTTP

        p = self._make_presenter(protocol_picker=picker)
        orig_add = p.add_new_tab

        def wrapped_add(*args, **kwargs):
            order.append("editor")
            return orig_add(*args, **kwargs)

        p.add_new_tab = wrapped_add
        p.handle_new_tab("shortcut")
        self.assertIn("picker", order)
        self.assertEqual(order[0], "picker")

        order.clear()
        p.handle_new_tab("plus_button")
        self.assertIn("picker", order)
        self.assertEqual(order[0], "picker")

    def test_handle_new_tab_http_is_default_first_item(self):
        menu = NewTabProtocolPicker().build_menu()
        labels = [action.text().replace("&", "") for action in menu.actions()]
        self.assertEqual(
            labels,
            ["HTTP Request", "WebSocket", "MCP Client"],
        )
        self.assertIs(menu.activeAction(), menu.actions()[0])

    def test_handle_new_tab_cancel_does_not_create_tab(self):
        p = self._make_presenter(protocol_picker=lambda *_a, **_k: None)
        before_count = p.widget.count()
        before_current = p.widget.currentWidget()
        before_editors = [id(w) for w in self._editor_tabs(p)]
        p._metrics.track_gui_new_tab_action.reset_mock()
        p.handle_new_tab("shortcut")
        self.assertEqual(p.widget.count(), before_count)
        self.assertIs(p.widget.currentWidget(), before_current)
        self.assertEqual(
            [id(w) for w in self._editor_tabs(p)],
            before_editors,
        )
        p._metrics.track_gui_new_tab_action.assert_not_called()

    def test_handle_new_tab_cancel_logs_source_without_metric(self):
        p = self._make_presenter(protocol_picker=lambda *_a, **_k: None)
        p._metrics.track_gui_new_tab_action.reset_mock()
        logger_name = "pypost.ui.presenters.tabs_presenter"
        with self.assertLogs(logger_name, level="INFO") as caplog:
            p.handle_new_tab("shortcut")
        joined = "\n".join(caplog.output)
        self.assertIn("new_tab_action_triggered source=shortcut", joined)
        self.assertIn("new_tab_action_cancelled source=shortcut", joined)
        self.assertNotIn("new_tab_action_completed", joined)
        self.assertNotIn("url=", joined)
        p._metrics.track_gui_new_tab_action.assert_not_called()

    def test_handle_new_tab_confirm_logs_source_and_protocol(self):
        logger_name = "pypost.ui.presenters.tabs_presenter"
        p_http = self._make_presenter(
            protocol_picker=lambda *_a, **_k: TabProtocol.HTTP,
        )
        with self.assertLogs(logger_name, level="INFO") as caplog:
            p_http.handle_new_tab("shortcut")
        http_logs = "\n".join(caplog.output)
        self.assertIn("new_tab_action_triggered source=shortcut", http_logs)
        self.assertIn(
            "new_tab_action_completed source=shortcut protocol=http",
            http_logs,
        )
        self.assertNotIn("new_tab_action_cancelled", http_logs)
        self.assertNotIn("url=", http_logs)

        p_ws = self._make_presenter(
            protocol_picker=lambda *_a, **_k: TabProtocol.WEBSOCKET,
        )
        with self.assertLogs(logger_name, level="INFO") as caplog:
            p_ws.handle_new_tab("plus_button")
        ws_logs = "\n".join(caplog.output)
        self.assertIn("new_tab_action_triggered source=plus_button", ws_logs)
        self.assertIn(
            "new_tab_action_completed source=plus_button protocol=websocket",
            ws_logs,
        )
        self.assertNotIn("new_tab_action_cancelled", ws_logs)
        self.assertNotIn("url=", ws_logs)

    def test_handle_new_tab_websocket_confirm_opens_ws_blank_not_request_tab(
        self,
    ):
        def picker(*_a, **_k):
            return TabProtocol.WEBSOCKET

        p = self._make_presenter(protocol_picker=picker)
        with patch.object(p, "open_websocket_tab") as mock_open_saved:
            p.handle_new_tab("plus_button")
        current = p.widget.currentWidget()
        self.assertNotIsInstance(current, RequestTab)
        self.assertIsInstance(current, WebSocketTab)
        mock_open_saved.assert_not_called()

    def test_handle_new_tab_http_confirm_opens_request_tab(self):
        calls = []

        def picker(*_a, **_k):
            calls.append(True)
            return TabProtocol.HTTP

        p = self._make_presenter(protocol_picker=picker)
        p.handle_new_tab("shortcut")
        self.assertEqual(len(calls), 1)
        current = p.widget.currentWidget()
        self.assertIsInstance(current, RequestTab)
        index = p.widget.indexOf(current)
        self.assertEqual(p.widget.tabText(index), "New Request")

    def test_open_blank_tab_records_source_and_protocol(self):
        p = self._make_presenter()
        p._metrics.track_gui_new_tab_action.reset_mock()
        p.open_blank_tab(TabProtocol.HTTP, "shortcut")
        self._assert_new_tab_metric(
            p._metrics.track_gui_new_tab_action,
            "shortcut",
            "http",
        )
        p._metrics.track_gui_new_tab_action.reset_mock()
        p.open_blank_tab(TabProtocol.WEBSOCKET, "plus_button")
        self._assert_new_tab_metric(
            p._metrics.track_gui_new_tab_action,
            "plus_button",
            "websocket",
        )

    def test_handle_new_tab_mcp_client_confirm_opens_mcp_tab_not_http(self):
        def picker(*_a, **_k):
            return TabProtocol.MCP_CLIENT

        for source in ("shortcut", "plus_button"):
            p = self._make_presenter(protocol_picker=picker)
            orig_add = p.add_new_tab
            add_http_calls = []

            def wrapped_add(*args, **kwargs):
                add_http_calls.append(True)
                return orig_add(*args, **kwargs)

            p.add_new_tab = wrapped_add
            with patch.object(p, "open_websocket_tab") as mock_open_saved:
                p.handle_new_tab(source)
            current = p.widget.currentWidget()
            self.assertNotIsInstance(current, RequestTab)
            self.assertNotIsInstance(current, WebSocketTab)
            self.assertIsInstance(current, McpClientTab)
            self.assertEqual(add_http_calls, [])
            mock_open_saved.assert_not_called()

    def test_open_blank_tab_mcp_client_does_not_fall_through_to_http(self):
        p = self._make_presenter()
        orig_add = p.add_new_tab
        add_http_calls = []

        def wrapped_add(*args, **kwargs):
            add_http_calls.append(True)
            return orig_add(*args, **kwargs)

        p.add_new_tab = wrapped_add
        p.open_blank_tab(TabProtocol.MCP_CLIENT, "shortcut")
        current = p.widget.currentWidget()
        self.assertNotIsInstance(current, RequestTab)
        self.assertNotIsInstance(current, WebSocketTab)
        self.assertIsInstance(current, McpClientTab)
        self.assertEqual(add_http_calls, [])

    def test_open_blank_tab_mcp_client_sets_title_new_mcp_client(self):
        """PYPOST-1183: blank MCP open sets strip title New MCP Client."""
        p = self._make_presenter()
        p.open_blank_tab(TabProtocol.MCP_CLIENT, "shortcut")
        current = p.widget.currentWidget()
        self.assertIsInstance(current, McpClientTab)
        index = p.widget.indexOf(current)
        self.assertEqual(p.widget.tabText(index), "New MCP Client")

    def test_open_blank_tab_mcp_client_sets_widget_id(self):
        """PYPOST-1183: blank MCP open keeps MCP_CLIENT_TAB_PAGE identity."""
        p = self._make_presenter()
        p.open_blank_tab(TabProtocol.MCP_CLIENT, "shortcut")
        current = p.widget.currentWidget()
        self.assertIsInstance(current, McpClientTab)
        self.assertEqual(current.objectName(), MCP_CLIENT_TAB_PAGE)
        self.assertEqual(current.objectName(), "pypost_mcp_client_tab_page")

    def test_request_tab_count_helper_counts_mcp_client(self):
        """PYPOST-1183 FR-4: suite helper counts MCP like production."""
        p = self._make_presenter()
        p.add_blank_mcp_client_tab()
        self.assertGreaterEqual(_request_tab_count(p), 1)
        self.assertEqual(_request_tab_count(p), p._request_tab_count())

        p.add_new_tab()
        self.assertEqual(_request_tab_count(p), 2)
        self.assertEqual(_request_tab_count(p), p._request_tab_count())

        http_idx = next(
            i
            for i in range(p.widget.count())
            if isinstance(p.widget.widget(i), RequestTab)
        )
        p.close_tab(http_idx)
        self.assertGreaterEqual(_request_tab_count(p), 1)
        self.assertEqual(_request_tab_count(p), p._request_tab_count())
        self.assertIsInstance(p.widget.currentWidget(), McpClientTab)

    def test_open_blank_tab_records_mcp_client_protocol(self):
        def picker(*_a, **_k):
            return TabProtocol.MCP_CLIENT

        for source in ("shortcut", "plus_button"):
            p = self._make_presenter(protocol_picker=picker)
            p._metrics.track_gui_new_tab_action.reset_mock()
            p.handle_new_tab(source)
            self.assertIsInstance(p.widget.currentWidget(), McpClientTab)
            self._assert_new_tab_metric(
                p._metrics.track_gui_new_tab_action,
                source,
                "mcp_client",
            )

    def test_handle_new_tab_http_is_still_first_default(self):
        menu = NewTabProtocolPicker().build_menu()
        labels = [
            action.text().replace("&", "") for action in menu.actions()
        ]
        self.assertEqual(
            labels,
            ["HTTP Request", "WebSocket", "MCP Client"],
        )
        self.assertIs(menu.activeAction(), menu.actions()[0])
        self.assertEqual(menu.actions()[0].data(), TabProtocol.HTTP)


@pytest.mark.usefixtures("qapp")
class TestCloseLastTabProtocolPicker(unittest.TestCase):
    """PYPOST-1159: last-tab close uses handle_new_tab, not silent HTTP."""

    def _make_presenter(self, protocol_picker=None):
        return TabsPresenter(
            FakeRequestManager(),
            FakeStateManager(),
            AppSettings(),
            metrics=MagicMock(),
            protocol_picker=protocol_picker,
        )

    def _assert_new_tab_metric(self, mock_track, source, protocol):
        mock_track.assert_called()
        args, kwargs = mock_track.call_args
        got_source = args[0] if args else kwargs.get("source")
        if len(args) > 1:
            got_protocol = args[1]
        else:
            got_protocol = kwargs.get("protocol")
        self.assertEqual(got_source, source)
        self.assertEqual(got_protocol, protocol)

    def test_close_last_tab_uses_protocol_picker(self):
        order = []

        def picker(*_args, **_kwargs):
            order.append("picker")
            return TabProtocol.HTTP

        p = self._make_presenter(protocol_picker=picker)
        p.add_new_tab()
        orig_add = p.add_new_tab

        def wrapped_add(*args, **kwargs):
            order.append("editor")
            return orig_add(*args, **kwargs)

        p.add_new_tab = wrapped_add
        with patch.object(
            p, "handle_new_tab", wraps=p.handle_new_tab,
        ) as mock_handle:
            p.close_tab(0)
        mock_handle.assert_called_once_with("last_tab")
        self.assertIn("picker", order)
        self.assertEqual(order[0], "picker")

    def test_close_last_tab_http_confirm_opens_request_tab(self):
        calls = []

        def picker(*_a, **_k):
            calls.append(True)
            return TabProtocol.HTTP

        p = self._make_presenter(protocol_picker=picker)
        p.add_new_tab()
        p._metrics.track_gui_new_tab_action.reset_mock()
        p.close_tab(0)
        self.assertEqual(len(calls), 1)
        current = p.widget.currentWidget()
        self.assertIsInstance(current, RequestTab)
        index = p.widget.indexOf(current)
        self.assertEqual(p.widget.tabText(index), "New Request")
        self._assert_new_tab_metric(
            p._metrics.track_gui_new_tab_action,
            "last_tab",
            "http",
        )

    def test_close_last_tab_websocket_confirm_opens_ws_draft(self):
        def picker(*_a, **_k):
            return TabProtocol.WEBSOCKET

        p = self._make_presenter(protocol_picker=picker)
        p.add_new_tab()
        with patch.object(p, "open_websocket_tab") as mock_open_saved:
            p.close_tab(0)
        current = p.widget.currentWidget()
        self.assertNotIsInstance(current, RequestTab)
        self.assertIsInstance(current, WebSocketTab)
        mock_open_saved.assert_not_called()

    def test_close_last_tab_cancel_creates_no_replacement(self):
        p = self._make_presenter(
            protocol_picker=lambda *_a, **_k: None,
        )
        p.add_new_tab()
        p._metrics.track_gui_new_tab_action.reset_mock()
        p.close_tab(0)
        self.assertEqual(p._request_tab_count(), 0)
        p._metrics.track_gui_new_tab_action.assert_not_called()

    def test_close_non_last_tab_does_not_show_picker(self):
        calls = []

        def picker(*_a, **_k):
            calls.append(True)
            return TabProtocol.HTTP

        p = self._make_presenter(protocol_picker=picker)
        p.add_new_tab()
        p.add_new_tab()
        self.assertEqual(p._request_tab_count(), 2)
        p.close_tab(0)
        self.assertEqual(len(calls), 0)
        self.assertEqual(p._request_tab_count(), 1)

    def test_close_last_http_with_mcp_remaining_does_not_auto_open_http(self):
        """PYPOST-1183: closing last HTTP while MCP remains skips last_tab."""
        p = self._make_presenter(
            protocol_picker=lambda *_a, **_k: TabProtocol.HTTP,
        )
        p.add_new_tab()
        mcp_tab = p.add_blank_mcp_client_tab()
        http_idx = next(
            i
            for i in range(p.widget.count())
            if isinstance(p.widget.widget(i), RequestTab)
        )
        self.assertEqual(p._request_tab_count(), 2)
        self.assertEqual(_request_tab_count(p), 2)

        orig_add = p.add_new_tab
        add_http_calls = []

        def wrapped_add(*args, **kwargs):
            add_http_calls.append(True)
            return orig_add(*args, **kwargs)

        p.add_new_tab = wrapped_add
        with patch.object(
            p, "handle_new_tab", wraps=p.handle_new_tab,
        ) as mock_handle:
            p.close_tab(http_idx)

        mock_handle.assert_not_called()
        self.assertEqual(add_http_calls, [])
        self.assertIs(p.widget.currentWidget(), mcp_tab)
        self.assertIsInstance(p.widget.currentWidget(), McpClientTab)
        for i in range(p.widget.count()):
            self.assertNotIsInstance(p.widget.widget(i), RequestTab)
        self.assertGreaterEqual(p._request_tab_count(), 1)
        self.assertGreaterEqual(_request_tab_count(p), 1)
        self.assertEqual(_request_tab_count(p), p._request_tab_count())

    def test_close_dirty_last_websocket_draft_keep_skips_picker(self):
        calls = []

        def picker(*_a, **_k):
            calls.append(True)
            return TabProtocol.HTTP

        p = self._make_presenter(protocol_picker=picker)
        tab = p.add_blank_websocket_tab()
        tab.connection_editor.url_input.setText("ws://example.com/stream")
        idx = p.widget.indexOf(tab)
        prompt_path = (
            "pypost.ui.presenters.tabs_presenter.prompt_unsaved_draft_tab_close"
        )
        with patch(prompt_path, return_value=False) as prompt:
            p.close_tab(idx)
        prompt.assert_called_once()
        self.assertEqual(len(calls), 0)
        self.assertEqual(p.widget.indexOf(tab), idx)

    def test_close_dirty_last_websocket_draft_discard_then_picker(self):
        order = []

        def picker(*_a, **_k):
            order.append("picker")
            return TabProtocol.HTTP

        p = self._make_presenter(protocol_picker=picker)
        tab = p.add_blank_websocket_tab()
        tab.connection_editor.url_input.setText("ws://example.com/stream")
        idx = p.widget.indexOf(tab)
        prompt_path = (
            "pypost.ui.presenters.tabs_presenter.prompt_unsaved_draft_tab_close"
        )

        def prompt_discard(*_a, **_k):
            order.append("discard")
            return True

        with patch(prompt_path, side_effect=prompt_discard):
            p.close_tab(idx)
        self.assertIn("picker", order)
        self.assertEqual(order[0], "discard")
        self.assertEqual(order[1], "picker")
        self.assertEqual(p.widget.indexOf(tab), -1)


@pytest.mark.usefixtures("qapp")
class TestTabsPresenterWebSocketCollections(unittest.TestCase):
    """PYPOST-1160: WebSocket isolated tab open, rename, and delete-close (red until Step 4)."""

    def _make_presenter(self):
        return TabsPresenter(
            FakeRequestManager(),
            FakeStateManager(),
            AppSettings(),
            metrics=MagicMock(),
            protocol_picker=lambda *_a, **_k: TabProtocol.HTTP,
        )

    def _websocket_tab_count(self, presenter: TabsPresenter) -> int:
        return sum(
            1
            for i in range(presenter.widget.count())
            if isinstance(presenter.widget.widget(i), WebSocketTab)
        )

    def test_open_websocket_isolated_tab_always_inserts_second_tab(self):
        """Isolated open always inserts a new tab even when profile is already open."""
        p = self._make_presenter()
        conn = WebSocketConnection(id="ws-1", name="Live Feed")
        tab_a = p.open_websocket_tab(conn)
        tab_b = p.open_websocket_isolated_tab(conn.model_copy(deep=True))
        self.assertIsNot(tab_a, tab_b)
        self.assertEqual(tab_a.connection_data.id, tab_b.connection_data.id)
        self.assertEqual(self._websocket_tab_count(p), 2)

    def test_open_websocket_isolated_tabs_have_independent_presenters(self):
        """Isolated tabs from the same profile id have distinct session controllers."""
        p = self._make_presenter()
        conn = WebSocketConnection(id="ws-1", name="Live Feed")
        copy_a = conn.model_copy(deep=True)
        copy_b = conn.model_copy(deep=True)
        tab_a = p.open_websocket_isolated_tab(copy_a)
        tab_b = p.open_websocket_isolated_tab(copy_b)
        self.assertNotEqual(tab_a.presenter._session_id, tab_b.presenter._session_id)
        self.assertIsNot(tab_a.presenter._session_controller, tab_b.presenter._session_controller)

    def test_rename_websocket_tabs_updates_labels(self):
        """rename_websocket_tabs updates all matching WebSocketTab header labels."""
        p = self._make_presenter()
        conn = WebSocketConnection(id="ws-1", name="Old Name")
        p.open_websocket_tab(conn)
        p.open_websocket_isolated_tab(conn.model_copy(deep=True))
        p.rename_websocket_tabs("ws-1", "Renamed")
        labels = [
            p.widget.tabText(i)
            for i in range(p.widget.count())
            if isinstance(p.widget.widget(i), WebSocketTab)
        ]
        self.assertEqual(labels, ["Renamed", "Renamed"])

    def test_close_tabs_for_websocket_ids_silent_when_clean_idle(self):
        """Idle, non-dirty saved websocket tab closes without a delete prompt."""
        p = self._make_presenter()
        conn = WebSocketConnection(
            id="ws-1",
            name="Clean Feed",
            url="wss://example.com/stream",
        )
        tab = p.open_websocket_tab(conn, save_state=False)
        prompt_path = (
            "pypost.ui.presenters.tabs_presenter.prompt_deleted_websocket_profile_tab_close"
        )
        with patch(prompt_path, create=True) as prompt:
            p.close_tabs_for_websocket_ids(["ws-1"])
        prompt.assert_not_called()
        self.assertEqual(p.widget.indexOf(tab), -1)
        self.assertEqual(self._websocket_tab_count(p), 0)

    def test_close_tabs_for_websocket_ids_prompts_when_connected(self):
        """Active websocket session triggers delete prompt; cancel keeps the tab."""
        from pypost.core.websocket_session_policy import SessionState

        p = self._make_presenter()
        conn = WebSocketConnection(id="ws-1", name="Active Feed")
        tab = p.open_websocket_tab(conn, save_state=False)
        tab.presenter._state = SessionState.OPEN
        prompt_path = (
            "pypost.ui.presenters.tabs_presenter.prompt_deleted_websocket_profile_tab_close"
        )
        with patch(prompt_path, create=True, return_value=False) as prompt:
            p.close_tabs_for_websocket_ids(["ws-1"])
        prompt.assert_called_once()
        self.assertGreaterEqual(p.widget.indexOf(tab), 0)


@pytest.mark.usefixtures("qapp")
class TestWebsocketSaveSignals(unittest.TestCase):
    """PYPOST-1161: TabsPresenter WebSocket save / save-as signal wiring (red until Step 4)."""

    def _make_presenter(self):
        from pypost.models.models import Collection

        rm = FakeRequestManager()
        sm = FakeStateManager()
        rm.collections = [Collection(id="c1", name="Streams", websockets=[])]
        return TabsPresenter(rm, sm, AppSettings(), metrics=MagicMock()), rm, sm

    def test_websocket_save_emits_websocket_saved(self):
        p, _rm, sm = self._make_presenter()
        tab = p.add_blank_websocket_tab(save_state=False)
        draft_id = tab.connection_data.id

        self.assertTrue(
            hasattr(p, "websocket_saved"),
            "TabsPresenter.websocket_saved signal missing (PYPOST-1161)",
        )
        self.assertTrue(
            hasattr(p, "_handle_save_websocket"),
            "TabsPresenter._handle_save_websocket missing (PYPOST-1161)",
        )

        saved_received = []
        p.websocket_saved.connect(lambda: saved_received.append(True))
        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = True
        mock_dialog.selected_collection_id = "c1"
        mock_dialog.new_collection_name = ""
        mock_dialog.request_name = "Saved Feed"

        with patch(
            "pypost.ui.websocket_save_orchestrator.SaveRequestDialog",
            return_value=mock_dialog,
        ):
            p._handle_save_websocket(tab, tab.connection_data)

        self.assertEqual(saved_received, [True])
        self.assertEqual(tab.connection_data.name, "Saved Feed")
        self.assertEqual(tab.connection_data.id, draft_id)
        self.assertIn(draft_id, sm.get_open_tabs())

    def test_websocket_save_as_emits_save_as_completed(self):
        from pypost.models.models import Collection

        source = WebSocketConnection(
            id="ws-src",
            name="Source",
            url="wss://original.example.com",
        )
        col = Collection(id="c1", name="Streams", websockets=[source])
        rm = FakeRequestManager()
        rm.collections = [col]
        p = TabsPresenter(rm, FakeStateManager(), AppSettings(), metrics=MagicMock())
        tab = p.open_websocket_tab(source, save_state=False)

        self.assertTrue(
            hasattr(p, "websocket_save_as_completed"),
            "TabsPresenter.websocket_save_as_completed signal missing (PYPOST-1161)",
        )
        self.assertTrue(
            hasattr(p, "_handle_save_as_websocket"),
            "TabsPresenter._handle_save_as_websocket missing (PYPOST-1161)",
        )

        save_as_received = []
        saved_received = []
        p.websocket_save_as_completed.connect(
            lambda conn, collection_id: save_as_received.append(
                (conn.id, conn.name, collection_id)
            )
        )
        p.websocket_saved.connect(lambda: saved_received.append(True))

        mock_dialog = MagicMock()
        mock_dialog.exec.return_value = True
        mock_dialog.selected_collection_id = "c1"
        mock_dialog.new_collection_name = ""
        mock_dialog.request_name = "Copy"

        with patch(
            "pypost.ui.websocket_save_orchestrator.SaveRequestDialog",
            return_value=mock_dialog,
        ):
            p._handle_save_as_websocket(tab, tab.connection_data)

        self.assertEqual(len(save_as_received), 1)
        self.assertNotEqual(save_as_received[0][0], "ws-src")
        self.assertEqual(save_as_received[0][1], "Copy")
        self.assertEqual(save_as_received[0][2], "c1")
        self.assertEqual(saved_received, [])
        self.assertEqual(tab.connection_data.name, "Copy")
        self.assertNotEqual(tab.connection_data.id, "ws-src")


if __name__ == "__main__":
    unittest.main()

