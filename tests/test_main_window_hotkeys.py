"""Main-window hotkey routing tests for WebSocket session shortcuts (PYPOST-1162)."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from pypost.models.models import Collection
from pypost.models.settings import AppSettings
from pypost.ui.hotkeys import SECTION_ORDER
from pypost.ui.presenters.tabs_presenter import TabsPresenter, WebSocketTab
from pypost.ui.widgets.new_tab_protocol_picker import TabProtocol
from tests.test_request_save_orchestrator import _mock_save_dialog
from tests.test_tabs_presenter import FakeRequestManager, FakeStateManager

pytestmark = pytest.mark.timeout(120)


@pytest.mark.usefixtures("qapp")
class TestMainWindowWebSocketHotkeys(unittest.TestCase):
    """Context-aware dispatch when a WebSocket tab is active."""

    def _make_presenter(self) -> TabsPresenter:
        rm = FakeRequestManager()
        sm = FakeStateManager()
        return TabsPresenter(
            rm,
            sm,
            AppSettings(),
            metrics=MagicMock(),
            protocol_picker=lambda *_a, **_k: TabProtocol.HTTP,
        )

    def _add_ws_tab(self, presenter: TabsPresenter) -> WebSocketTab:
        tab = presenter.add_blank_websocket_tab(save_state=False)
        self.assertIsInstance(tab, WebSocketTab)
        return tab

    def test_section_order_includes_websocket_session(self):
        self.assertIn("WebSocket Session", SECTION_ORDER)

    def test_websocket_tab_ctrl_s_dispatches_save(self):
        presenter = self._make_presenter()
        col = Collection(id="c1", name="Streams", websockets=[])
        presenter._request_manager.collections = [col]
        tab = self._add_ws_tab(presenter)
        tab.setFocus()

        saved_signals: list[bool] = []
        presenter.websocket_saved.connect(lambda: saved_signals.append(True))
        mock_dialog = _mock_save_dialog(
            collection_id="c1",
            request_name="Hotkey Saved",
        )

        with patch(
            "pypost.ui.websocket_save_orchestrator.SaveRequestDialog",
            return_value=mock_dialog,
        ):
            tab.handle_save_request_shortcut()

        self.assertEqual(saved_signals, [True])

    def test_f5_on_websocket_tab_toggles_connect(self):
        presenter = self._make_presenter()
        tab = self._add_ws_tab(presenter)
        connect_spy = MagicMock()
        tab.presenter._on_connect_clicked = connect_spy

        presenter.handle_websocket_connect_global()

        connect_spy.assert_called_once()

    def test_ctrl_l_focuses_websocket_url_when_ws_tab_active(self):
        presenter = self._make_presenter()
        tab = self._add_ws_tab(presenter)
        presenter.widget.show()
        tab.show()
        QApplication.processEvents()
        url_input = tab.connection_editor.url_input
        url_input.setText("ws://example.com/stream")

        presenter.handle_focus_url()
        QApplication.processEvents()

        self.assertEqual(url_input.selectedText(), "ws://example.com/stream")

    def test_websocket_session_documentation_rows_registered(self):
        from PySide6.QtWidgets import QWidget

        from pypost.ui.hotkeys import collect_hotkey_rows, register_hotkey_documentation

        root = QWidget()
        register_hotkey_documentation(
            root,
            section="WebSocket Session",
            label="Connect / Disconnect",
            keys=("F5", "Ctrl+Return"),
            order=1,
        )
        sections = [label for label, key in collect_hotkey_rows(root) if not key]
        self.assertIn("WebSocket Session", sections)

    def test_request_editor_shortcuts_noop_on_websocket_tab(self):
        presenter = self._make_presenter()
        presenter.add_new_tab(save_state=False)
        request_tab = presenter._current_tab()
        self.assertIsNotNone(request_tab)
        request_tab.request_editor.detail_tabs.setCurrentIndex(2)

        presenter.add_blank_websocket_tab(save_state=False)
        self.assertIsInstance(presenter._tabs.currentWidget(), WebSocketTab)

        presenter.handle_switch_to_params_global()

        self.assertEqual(request_tab.request_editor.detail_tabs.currentIndex(), 2)


    def test_active_tab_kind_returns_websocket(self):
        presenter = self._make_presenter()
        self._add_ws_tab(presenter)
        self.assertEqual(presenter.active_tab_kind(), TabProtocol.WEBSOCKET)
