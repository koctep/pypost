"""Integration red tests for WebSocket save entry points (PYPOST-1161 / WS-TM-5).

Mirrors ``tests/test_save_flow_integration.py`` for WebSocketTab Actions / shortcuts.
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtGui import QKeySequence
from PySide6.QtTest import QTest

from pypost.models.models import Collection
from pypost.models.settings import AppSettings
from pypost.ui.presenters.tabs_presenter import TabsPresenter, WebSocketTab
from tests.test_request_save_orchestrator import _mock_save_dialog
from tests.test_tabs_presenter import FakeRequestManager, FakeStateManager

pytestmark = pytest.mark.timeout(120)


@pytest.mark.usefixtures("qapp")
class TestWebSocketSaveFlowIntegration(unittest.TestCase):
    """GUI entry points on WebSocketTab wired through TabsPresenter."""

    def _make_presenter(self):
        rm = FakeRequestManager()
        sm = FakeStateManager()
        return TabsPresenter(rm, sm, AppSettings(), metrics=MagicMock()), rm, sm

    def _active_ws_tab(self, presenter: TabsPresenter) -> WebSocketTab:
        tab = presenter.widget.currentWidget()
        self.assertIsInstance(tab, WebSocketTab)
        return tab

    def test_websocket_save_menu_updates_tab_identity(self):
        presenter, rm, sm = self._make_presenter()
        col = Collection(id="c1", name="Streams", websockets=[])
        rm.collections = [col]
        presenter.add_blank_websocket_tab(save_state=False)

        tab = self._active_ws_tab(presenter)
        draft_id = tab.connection_data.id
        self.assertTrue(
            hasattr(tab, "handle_save_menu_action") or hasattr(tab, "save_action"),
            "WebSocketTab must expose Actions Save (HTTP RequestWidget parity)",
        )
        self.assertTrue(
            hasattr(presenter, "websocket_saved"),
            "TabsPresenter.websocket_saved required after WS profile save",
        )
        if hasattr(tab.connection_editor, "url_input"):
            tab.connection_editor.url_input.setText("ws://draft.example.com")

        saved_signals = []
        presenter.websocket_saved.connect(lambda: saved_signals.append(True))
        mock_dialog = _mock_save_dialog(
            collection_id="c1",
            request_name="Persisted Feed",
        )

        with patch(
            "pypost.ui.websocket_save_orchestrator.SaveRequestDialog",
            return_value=mock_dialog,
        ):
            if hasattr(tab, "handle_save_menu_action"):
                tab.handle_save_menu_action()
            else:
                tab.save_action.trigger()

        self.assertEqual(saved_signals, [True])
        self.assertEqual(tab.connection_data.id, draft_id)
        self.assertEqual(tab.connection_data.name, "Persisted Feed")
        tab_index = presenter.widget.indexOf(tab)
        self.assertGreaterEqual(tab_index, 0)
        self.assertIn("Persisted Feed", presenter.widget.tabText(tab_index))
        self.assertIn(draft_id, sm.get_open_tabs())

    def test_websocket_ctrl_s_triggers_save(self):
        presenter, rm, _sm = self._make_presenter()
        col = Collection(id="c1", name="Streams", websockets=[])
        rm.collections = [col]
        presenter.add_blank_websocket_tab(save_state=False)

        tab = self._active_ws_tab(presenter)
        tab.setFocus()
        has_shortcut_handler = hasattr(tab, "handle_save_request_shortcut")
        has_save_action = hasattr(tab, "save_action")
        ctrl_s_actions = [
            action
            for action in tab.actions()
            if action.shortcut() == QKeySequence("Ctrl+S")
        ]
        self.assertTrue(
            has_shortcut_handler or has_save_action or bool(ctrl_s_actions),
            "WebSocketTab must expose Ctrl+S Save (FR-1.2)",
        )
        self.assertTrue(
            hasattr(presenter, "websocket_saved"),
            "TabsPresenter.websocket_saved required for Ctrl+S save path",
        )

        saved_signals = []
        presenter.websocket_saved.connect(lambda: saved_signals.append(True))
        mock_dialog = _mock_save_dialog(
            collection_id="c1",
            request_name="Hotkey Saved",
        )

        with patch(
            "pypost.ui.websocket_save_orchestrator.SaveRequestDialog",
            return_value=mock_dialog,
        ):
            if has_shortcut_handler:
                tab.handle_save_request_shortcut()
            elif has_save_action:
                tab.save_action.trigger()
            elif ctrl_s_actions:
                ctrl_s_actions[0].trigger()
            else:
                QTest.keySequence(tab, QKeySequence("Ctrl+S"))

        self.assertEqual(
            saved_signals,
            [True],
            "Ctrl+S / Save shortcut on a focused WebSocket tab must reach save",
        )


if __name__ == "__main__":
    unittest.main()
