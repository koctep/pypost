"""Main-window hotkey routing tests for WebSocket and MCP Client shortcuts."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from pypost.models.models import Collection
from pypost.models.settings import AppSettings
from pypost.ui.hotkeys import SECTION_ORDER
from pypost.ui.presenters.tabs_presenter import TabsPresenter, WebSocketTab
from pypost.ui.widgets.mcp_client import McpClientTab
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
            keys=("F5",),
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


@pytest.mark.usefixtures("qapp")
class TestMainWindowMcpClientHotkeys(unittest.TestCase):
    """Context-aware dispatch when an MCP Client tab is active."""

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

    def _add_mcp_tab(self, presenter: TabsPresenter) -> McpClientTab:
        tab = presenter.add_blank_mcp_client_tab(save_state=False)
        self.assertIsInstance(tab, McpClientTab)
        return tab

    def test_section_order_includes_mcp_client(self):
        self.assertIn("MCP Client", SECTION_ORDER)

    def test_mcp_client_tab_ctrl_s_dispatches_save(self):
        presenter = self._make_presenter()
        col = Collection(id="c1", name="MCP", mcp_clients=[])
        presenter._request_manager.collections = [col]
        tab = self._add_mcp_tab(presenter)
        tab.setFocus()

        saved_signals: list[bool] = []
        presenter.mcp_client_saved.connect(lambda: saved_signals.append(True))
        mock_dialog = _mock_save_dialog(
            collection_id="c1",
            request_name="Hotkey Saved",
        )

        with patch(
            "pypost.ui.mcp_client_save_orchestrator.SaveRequestDialog",
            return_value=mock_dialog,
        ):
            tab.handle_save_request_shortcut()

        self.assertEqual(saved_signals, [True])

    def test_f5_on_mcp_client_tab_toggles_connect(self):
        presenter = self._make_presenter()
        tab = self._add_mcp_tab(presenter)
        connect_spy = MagicMock()
        tab.presenter.connect_requested = connect_spy

        presenter.handle_mcp_client_connect_global()

        connect_spy.assert_called_once()

    def test_ctrl_l_focuses_mcp_client_url_when_mcp_tab_active(self):
        presenter = self._make_presenter()
        tab = self._add_mcp_tab(presenter)
        presenter.widget.show()
        tab.show()
        QApplication.processEvents()
        tab.url_input.setText("http://127.0.0.1:1080/mcp")

        presenter.handle_focus_url()
        QApplication.processEvents()

        self.assertEqual(tab.url_input.selectedText(), "http://127.0.0.1:1080/mcp")

    def test_mcp_client_session_documentation_rows_registered(self):
        from PySide6.QtWidgets import QWidget

        from pypost.ui.hotkeys import collect_hotkey_rows, register_hotkey_documentation

        root = QWidget()
        register_hotkey_documentation(
            root,
            section="MCP Client",
            label="Connect / Disconnect",
            keys=("F5",),
            order=1,
        )
        sections = [label for label, key in collect_hotkey_rows(root) if not key]
        self.assertIn("MCP Client", sections)

    def test_request_editor_shortcuts_noop_on_mcp_client_tab(self):
        presenter = self._make_presenter()
        presenter.add_new_tab(save_state=False)
        request_tab = presenter._current_tab()
        self.assertIsNotNone(request_tab)
        request_tab.request_editor.detail_tabs.setCurrentIndex(2)

        presenter.add_blank_mcp_client_tab(save_state=False)
        self.assertIsInstance(presenter._tabs.currentWidget(), McpClientTab)

        presenter.handle_switch_to_params_global()

        self.assertEqual(request_tab.request_editor.detail_tabs.currentIndex(), 2)

    def test_active_tab_kind_returns_mcp_client(self):
        presenter = self._make_presenter()
        self._add_mcp_tab(presenter)
        self.assertEqual(presenter.active_tab_kind(), TabProtocol.MCP_CLIENT)

    def test_invoke_global_dispatches_presenter(self):
        presenter = self._make_presenter()
        tab = self._add_mcp_tab(presenter)
        invoke_spy = MagicMock()
        tab.presenter.invoke_requested = invoke_spy

        presenter.handle_mcp_client_invoke_global()

        invoke_spy.assert_called_once()


# ---------------------------------------------------------------------------
# PYPOST-1285: Ctrl+Return / F5 disambiguation (groups A-D, F)
# ---------------------------------------------------------------------------

_KEY_SLOTS = {"F5": "handle_f5_global", "Ctrl+Return": "handle_ctrl_return_global"}


def _press(presenter, key: str) -> None:
    """Invoke the presenter slot bound to ``key``."""
    getattr(presenter, _KEY_SLOTS[key])()


def _focus(widget):
    """Make ``QApplication.focusWidget()`` deterministic offscreen."""
    return patch.object(QApplication, "focusWidget", return_value=widget)


def _make_tabs_presenter() -> TabsPresenter:
    return TabsPresenter(
        FakeRequestManager(),
        FakeStateManager(),
        AppSettings(),
        metrics=MagicMock(),
        protocol_picker=lambda *_a, **_k: TabProtocol.HTTP,
    )


@pytest.mark.usefixtures("qapp")
class TestCtrlReturnF5RoutingWebSocket(unittest.TestCase):
    """PYPOST-1285 group A: WS Ctrl+Return only sends, F5 only toggles, any focus."""

    def setUp(self) -> None:
        from pypost.core.websocket_session_policy import SessionState

        self.SessionState = SessionState
        self.presenter = _make_tabs_presenter()
        self.tab = self.presenter.add_blank_websocket_tab(save_state=False)
        self.assertIsInstance(self.tab, WebSocketTab)
        self.assertEqual(self.tab.presenter.state, SessionState.IDLE)
        self.url_input = self.tab.connection_editor.url_input
        self.payload_edit = self.tab.composer.payload_edit

    def _spy_idle(self) -> tuple[MagicMock, MagicMock]:
        send_spy = MagicMock()
        connect_spy = MagicMock()
        self.tab.presenter.handle_send_message = send_spy
        self.tab.presenter._on_connect_clicked = connect_spy
        return send_spy, connect_spy

    def _spy_open(self) -> tuple[MagicMock, MagicMock, MagicMock]:
        self.tab.presenter._current_state = self.SessionState.OPEN
        send_spy = MagicMock()
        disconnect_spy = MagicMock()
        connect_spy = MagicMock()
        self.tab.presenter.handle_send_message = send_spy
        self.tab.presenter.handle_disconnect = disconnect_spy
        self.tab.presenter.handle_connect = connect_spy
        return send_spy, disconnect_spy, connect_spy

    # -- disconnected (IDLE) ------------------------------------------------

    def test_ctrl_return_outside_composer_sends_not_toggles(self):
        """Ctrl+Return outside the composer sends, not toggles Connect."""
        send_spy, connect_spy = self._spy_idle()
        with _focus(self.url_input):
            _press(self.presenter, "Ctrl+Return")
        self.assertEqual(connect_spy.call_count, 0, "Ctrl+Return toggled Connect")
        self.assertEqual(send_spy.call_count, 1)

    def test_ctrl_return_with_no_focus_sends_not_toggles(self):
        """Ctrl+Return with no focus sends, not toggles Connect."""
        send_spy, connect_spy = self._spy_idle()
        with _focus(None):
            _press(self.presenter, "Ctrl+Return")
        self.assertEqual(connect_spy.call_count, 0, "Ctrl+Return toggled Connect")
        self.assertEqual(send_spy.call_count, 1)

    def test_ctrl_return_in_composer_sends(self):
        """Ctrl+Return in the composer sends."""
        send_spy, connect_spy = self._spy_idle()
        with _focus(self.payload_edit):
            _press(self.presenter, "Ctrl+Return")
        self.assertEqual(send_spy.call_count, 1)
        self.assertEqual(connect_spy.call_count, 0)

    def test_ctrl_return_disconnected_does_not_connect(self):
        """A blocked send (IDLE) must not open a connection."""
        connect_spy = MagicMock()
        disconnect_spy = MagicMock()
        self.tab.presenter.handle_connect = connect_spy
        self.tab.presenter.handle_disconnect = disconnect_spy
        with _focus(self.url_input):
            _press(self.presenter, "Ctrl+Return")
        self.assertEqual(connect_spy.call_count, 0, "Ctrl+Return started a connection")
        self.assertEqual(disconnect_spy.call_count, 0)
        self.assertEqual(self.tab.presenter.state, self.SessionState.IDLE)

    def test_f5_in_composer_toggles_not_sends(self):
        """F5 in the composer toggles Connect, not sends."""
        send_spy, connect_spy = self._spy_idle()
        with _focus(self.payload_edit):
            _press(self.presenter, "F5")
        self.assertEqual(send_spy.call_count, 0, "F5 sent a message")
        self.assertEqual(connect_spy.call_count, 1)

    def test_f5_outside_composer_toggles(self):
        """F5 outside the composer / with no focus toggles Connect."""
        for focus in (self.url_input, None):
            with self.subTest(focus=focus):
                send_spy, connect_spy = self._spy_idle()
                with _focus(focus):
                    _press(self.presenter, "F5")
                self.assertEqual(connect_spy.call_count, 1)
                self.assertEqual(send_spy.call_count, 0)

    # -- connected (OPEN) ---------------------------------------------------

    def test_ctrl_return_open_outside_composer_does_not_disconnect(self):
        """Ctrl+Return outside the composer sends, not disconnects, while OPEN."""
        for focus in (self.url_input, None):
            with self.subTest(focus=focus):
                send_spy, disconnect_spy, connect_spy = self._spy_open()
                with _focus(focus):
                    _press(self.presenter, "Ctrl+Return")
                self.assertEqual(
                    disconnect_spy.call_count, 0, "Ctrl+Return disconnected the session"
                )
                self.assertEqual(connect_spy.call_count, 0)
                self.assertEqual(send_spy.call_count, 1)

    def test_ctrl_return_open_in_composer_sends_not_disconnects(self):
        """Ctrl+Return in the composer sends while OPEN."""
        send_spy, disconnect_spy, _connect_spy = self._spy_open()
        with _focus(self.payload_edit):
            _press(self.presenter, "Ctrl+Return")
        self.assertEqual(send_spy.call_count, 1)
        self.assertEqual(disconnect_spy.call_count, 0)

    def test_f5_open_in_composer_disconnects_not_sends(self):
        """F5 in the composer disconnects, not sends, while OPEN."""
        send_spy, disconnect_spy, _connect_spy = self._spy_open()
        with _focus(self.payload_edit):
            _press(self.presenter, "F5")
        self.assertEqual(send_spy.call_count, 0, "F5 sent a message")
        self.assertEqual(disconnect_spy.call_count, 1)

    def test_f5_open_outside_composer_disconnects(self):
        """F5 outside the composer / with no focus disconnects while OPEN."""
        for focus in (self.url_input, None):
            with self.subTest(focus=focus):
                send_spy, disconnect_spy, _connect_spy = self._spy_open()
                with _focus(focus):
                    _press(self.presenter, "F5")
                self.assertEqual(disconnect_spy.call_count, 1)
                self.assertEqual(send_spy.call_count, 0)


@pytest.mark.usefixtures("qapp")
class TestCtrlReturnF5RoutingMcpClient(unittest.TestCase):
    """PYPOST-1285 group B: MCP Ctrl+Return only invokes, F5 only toggles, any focus."""

    def setUp(self) -> None:
        from PySide6.QtWidgets import QWidget

        from pypost.models.mcp_client import McpClientSessionState

        self.State = McpClientSessionState
        self.presenter = _make_tabs_presenter()
        self.tab = self.presenter.add_blank_mcp_client_tab(save_state=False)
        self.assertIsInstance(self.tab, McpClientTab)
        self.assertEqual(self.tab.presenter.state, McpClientSessionState.DISCONNECTED)
        children = self.tab.invoke_form.findChildren(QWidget)
        self.form_child = children[0] if children else self.tab.invoke_form
        self.invoke_spy = MagicMock()
        self.connect_spy = MagicMock()
        self.disconnect_spy = MagicMock()
        self.tab.presenter.invoke_requested = self.invoke_spy
        self.tab.presenter.connect_requested = self.connect_spy
        self.tab.presenter.disconnect_requested = self.disconnect_spy

    def _set_connected(self) -> None:
        self.tab.presenter._state = self.State.CONNECTED
        self.assertEqual(self.tab.presenter.state, self.State.CONNECTED)

    def test_ctrl_return_outside_invoke_form_invokes_not_toggles(self):
        """Ctrl+Return outside the invoke form invokes, not toggles Connect."""
        with _focus(self.tab.url_input):
            _press(self.presenter, "Ctrl+Return")
        self.assertEqual(self.connect_spy.call_count, 0, "Ctrl+Return toggled Connect")
        self.assertEqual(self.invoke_spy.call_count, 1)

    def test_ctrl_return_connected_outside_form_does_not_disconnect(self):
        """Ctrl+Return with no focus invokes, not disconnects, while CONNECTED."""
        self._set_connected()
        with _focus(None):
            _press(self.presenter, "Ctrl+Return")
        self.assertEqual(
            self.disconnect_spy.call_count, 0, "Ctrl+Return disconnected the session"
        )
        self.assertEqual(self.invoke_spy.call_count, 1)

    def test_ctrl_return_in_invoke_form_invokes(self):
        """Ctrl+Return inside the invoke form invokes."""
        with _focus(self.form_child):
            _press(self.presenter, "Ctrl+Return")
        self.assertEqual(self.invoke_spy.call_count, 1)
        self.assertEqual(self.connect_spy.call_count, 0)

    def test_f5_in_invoke_form_toggles_not_invokes(self):
        """F5 inside the invoke form toggles Connect, not invokes."""
        with _focus(self.form_child):
            _press(self.presenter, "F5")
        self.assertEqual(self.invoke_spy.call_count, 0, "F5 invoked a tool")
        self.assertEqual(self.connect_spy.call_count, 1)

    def test_f5_connected_in_invoke_form_disconnects(self):
        """F5 inside the invoke form disconnects, not invokes, while CONNECTED."""
        self._set_connected()
        with _focus(self.form_child):
            _press(self.presenter, "F5")
        self.assertEqual(self.invoke_spy.call_count, 0, "F5 invoked a tool")
        self.assertEqual(self.disconnect_spy.call_count, 1)


@pytest.mark.usefixtures("qapp")
class TestCtrlReturnF5RoutingHttp(unittest.TestCase):
    """PYPOST-1285 group C: HTTP regression guards."""

    def test_f5_sends_http_request(self):
        presenter = _make_tabs_presenter()
        presenter.add_new_tab(save_state=False)
        tab = presenter._current_tab()
        self.assertIsNotNone(tab)
        send_spy = MagicMock()
        tab.request_editor.on_send = send_spy
        _press(presenter, "F5")
        send_spy.assert_called_once()

    def test_ctrl_return_sends_http_request(self):
        presenter = _make_tabs_presenter()
        presenter.add_new_tab(save_state=False)
        tab = presenter._current_tab()
        self.assertIsNotNone(tab)
        send_spy = MagicMock()
        tab.request_editor.on_send = send_spy
        _press(presenter, "Ctrl+Return")
        send_spy.assert_called_once()

    def test_keys_noop_without_tabs(self):
        presenter = _make_tabs_presenter()
        self.assertIsNone(presenter.active_tab_kind())
        _press(presenter, "F5")
        _press(presenter, "Ctrl+Return")


_ROUTING_LOGGER = "pypost.ui.presenters.tabs_presenter_hotkeys"


@pytest.mark.usefixtures("qapp")
class TestHotkeyRoutedLogging(unittest.TestCase):
    """PYPOST-1285 Step 6: ``hotkey_routed`` DEBUG event contract."""

    def _routed_lines(self, presenter, key: str) -> list[str]:
        with self.assertLogs(_ROUTING_LOGGER, level="DEBUG") as captured:
            _press(presenter, key)
        return [r.getMessage() for r in captured.records if r.msg.startswith("hotkey_routed")]

    def test_websocket_routes_logged_per_key(self):
        presenter = _make_tabs_presenter()
        tab = presenter.add_blank_websocket_tab(save_state=False)
        tab.presenter.handle_send_message = MagicMock()
        tab.presenter._on_connect_clicked = MagicMock()
        self.assertEqual(
            self._routed_lines(presenter, "F5"),
            ["hotkey_routed key=f5 tab_kind=websocket action=connect_toggle"],
        )
        self.assertEqual(
            self._routed_lines(presenter, "Ctrl+Return"),
            ["hotkey_routed key=ctrl_return tab_kind=websocket action=send_message"],
        )

    def test_mcp_client_routes_logged_per_key(self):
        presenter = _make_tabs_presenter()
        tab = presenter.add_blank_mcp_client_tab(save_state=False)
        tab.presenter.invoke_requested = MagicMock()
        tab.presenter.connect_requested = MagicMock()
        self.assertEqual(
            self._routed_lines(presenter, "F5"),
            ["hotkey_routed key=f5 tab_kind=mcp_client action=connect_toggle"],
        )
        self.assertEqual(
            self._routed_lines(presenter, "Ctrl+Return"),
            ["hotkey_routed key=ctrl_return tab_kind=mcp_client action=invoke_tool"],
        )

    def test_http_routes_logged_per_key(self):
        presenter = _make_tabs_presenter()
        presenter.add_new_tab(save_state=False)
        presenter._current_tab().request_editor.on_send = MagicMock()
        for key, name in (("F5", "f5"), ("Ctrl+Return", "ctrl_return")):
            self.assertEqual(
                self._routed_lines(presenter, key),
                [f"hotkey_routed key={name} tab_kind=http action=send_request"],
            )

    def test_no_tab_logged_as_noop(self):
        presenter = _make_tabs_presenter()
        self.assertEqual(
            self._routed_lines(presenter, "F5"),
            ["hotkey_routed key=f5 tab_kind=none action=noop"],
        )
        self.assertEqual(
            self._routed_lines(presenter, "Ctrl+Return"),
            ["hotkey_routed key=ctrl_return tab_kind=none action=noop"],
        )

    def test_early_return_logged_as_noop_with_reason(self):
        """A WS tab without a presenter runs nothing, so the label must not claim an action."""
        presenter = _make_tabs_presenter()
        tab = presenter.add_blank_websocket_tab(save_state=False)
        ws_presenter = tab.presenter
        tab.presenter = None  # type: ignore[assignment]
        try:
            for key, name in (("F5", "f5"), ("Ctrl+Return", "ctrl_return")):
                self.assertEqual(
                    self._routed_lines(presenter, key),
                    [
                        f"hotkey_routed key={name} tab_kind=websocket action=noop "
                        "reason=target_unavailable"
                    ],
                )
        finally:
            tab.presenter = ws_presenter

    def test_route_tables_cover_every_tab_kind(self):
        """Each send-key route table has a (label, handler) entry for every TabProtocol."""
        from pypost.ui.presenters import tabs_presenter_hotkeys as hk

        for routes in (hk._F5_ROUTES, hk._CTRL_RETURN_ROUTES):
            self.assertEqual(set(routes), set(TabProtocol))
            for label, handler in routes.values():
                self.assertTrue(label)
                self.assertTrue(callable(handler))


def _rows_by_section(rows: list[tuple[str, str]]) -> dict[str, dict[str, str]]:
    sections: dict[str, dict[str, str]] = {}
    current: dict[str, str] | None = None
    for label, display in rows:
        if not display:
            current = sections.setdefault(label, {})
            continue
        assert current is not None
        current[label] = display
    return sections


@pytest.mark.usefixtures("qapp")
class TestProtocolSessionHelpRows(unittest.TestCase):
    """PYPOST-1285 group D: Help -> Hotkeys rows for WS / MCP sessions."""

    def setUp(self) -> None:
        from PySide6.QtWidgets import QWidget

        from pypost.ui.hotkeys import collect_hotkey_rows
        from pypost.ui.main_window_protocol_hotkeys import register_protocol_session_hotkeys

        self.root = QWidget()
        register_protocol_session_hotkeys(self.root, MagicMock())
        self.sections = _rows_by_section(collect_hotkey_rows(self.root))

    def tearDown(self) -> None:
        self.root.deleteLater()

    def test_websocket_connect_row_lists_only_f5(self):
        """Connect / Disconnect row lists only F5."""
        self.assertEqual(self.sections["WebSocket Session"]["Connect / Disconnect"], "F5")

    def test_mcp_connect_row_lists_only_f5(self):
        """Connect / Disconnect row lists only F5."""
        self.assertEqual(self.sections["MCP Client"]["Connect / Disconnect"], "F5")

    def test_send_and_invoke_rows_list_native_ctrl_return(self):
        """Send / Invoke rows show the native Ctrl+Return text."""
        from PySide6.QtGui import QKeySequence

        native = QKeySequence("Ctrl+Return").toString(QKeySequence.SequenceFormat.NativeText)
        self.assertEqual(self.sections["WebSocket Session"]["Send Message"], native)
        self.assertEqual(self.sections["MCP Client"]["Invoke Tool"], native)

    def test_no_key_listed_twice_within_session_sections(self):
        """No key is listed under two rows of one session section."""
        for section in ("WebSocket Session", "MCP Client"):
            with self.subTest(section=section):
                keys: list[str] = []
                for display in self.sections[section].values():
                    keys.extend(display.split(" / "))
                duplicates = sorted({k for k in keys if keys.count(k) > 1})
                self.assertEqual(duplicates, [], f"{section} lists keys twice")

    def test_documentation_rows_bind_no_shortcut(self):
        """Display-only rows bind no live shortcut."""
        from PySide6.QtGui import QAction

        from pypost.ui.hotkeys import LABEL_PROPERTY, SECTION_PROPERTY

        bound: list[str] = []
        for action in self.root.actions():
            if not action.property(SECTION_PROPERTY):
                continue
            if action.text() == "Format JSON":
                continue
            self.assertIsInstance(action, QAction)
            if not action.shortcut().isEmpty():
                bound.append(
                    f"{action.property(SECTION_PROPERTY)}/{action.property(LABEL_PROPERTY)}"
                    f"={action.shortcut().toString()}"
                )
        self.assertEqual(bound, [], "documentation rows bind live shortcuts")


_ACTIVATION_SKIP = "window activation unavailable on this QPA platform"

# Help rows from collect_hotkey_rows(MainWindow) captured at 1b990ba5, excluding the
# WS / MCP "Connect / Disconnect" rows (changed by PYPOST-1285).
_EXPECTED_OTHER_HELP_ROWS: list[tuple[str, str]] = [
    ("General", ""),
    ("Quit Application", "Ctrl+Q"),
    ("Settings", "Ctrl+, / F12"),
    ("Environment Manager", "Ctrl+E"),
    ("Tabs", ""),
    ("New Tab", "Ctrl+N"),
    ("Close Tab", "Ctrl+W"),
    ("Next Tab", "Ctrl+Tab"),
    ("Previous Tab", "Ctrl+Shift+Tab"),
    ("Switch to Tab 1-9", "Alt+1 ... Alt+9"),
    ("Request Editor", ""),
    ("Send Request", "F5 / Ctrl+Return"),
    ("Focus URL Bar", "Ctrl+L / Alt+D"),
    ("Switch to Params", "Ctrl+P"),
    ("Switch to Headers", "Ctrl+H"),
    ("Switch to Body", "Ctrl+B"),
    ("Switch to Script", "Ctrl+T"),
    ("WebSocket Session", ""),
    ("Send Message", "Ctrl+Return"),
    ("Focus URL Bar", "Ctrl+L / Alt+D"),
    ("Format JSON", "Ctrl+Shift+F"),
    ("MCP Client", ""),
    ("Invoke Tool", "Ctrl+Return"),
    ("Focus URL Bar", "Ctrl+L / Alt+D"),
]


@pytest.mark.usefixtures("qapp")
class TestMainWindowSendKeyWiring(unittest.TestCase):
    """PYPOST-1285 group F: real MainWindow key events reach the key-specific routers."""

    def setUp(self) -> None:
        from PySide6.QtWidgets import QLineEdit, QVBoxLayout, QWidget

        from pypost.ui.main_window import MainWindow

        self.mock_tabs = MagicMock()
        mock_collections = MagicMock()
        history_panel = QWidget()
        self.focus_target = QLineEdit(history_panel)
        QVBoxLayout(history_panel).addWidget(self.focus_target)
        with (
            patch("pypost.ui.main_window.StorageManager"),
            patch("pypost.ui.main_window.ConfigManager"),
            patch("pypost.ui.main_window.RequestManager"),
            patch("pypost.ui.main_window.StateManager") as mock_sm,
            patch("pypost.ui.mcp_server_controller.MCPServerManager"),
            patch(
                "pypost.ui.main_window.CollectionsPresenter",
                return_value=mock_collections,
            ),
            patch("pypost.ui.main_window.TabsPresenter", return_value=self.mock_tabs),
            patch("pypost.ui.main_window.EnvPresenter") as mock_env_cls,
            patch("pypost.ui.main_window.HistoryPanel", return_value=history_panel),
            patch("pypost.ui.main_window.wire_presenter_signals"),
            patch("pypost.ui.main_window.MainWindow.apply_settings"),
            patch(
                "pypost.ui.main_window.resolve_encryption_enabled",
                return_value=False,
            ),
        ):
            mock_sm.return_value.settings = AppSettings()
            mock_collections.panel = QWidget()
            self.mock_tabs.widget = QWidget()
            mock_env_cls.return_value.widget = QWidget()
            self.window = MainWindow(
                metrics=MagicMock(),
                template_service=MagicMock(),
                history_manager=MagicMock(),
            )
        self._shown = False

    def tearDown(self) -> None:
        from pypost.core.lifecycle import TeardownResult

        self.window._shutdown_for_exit = lambda: TeardownResult("main_window", "success", 0)
        if self._shown:
            self.window.close()
            QApplication.processEvents()
            self.assertFalse(self.window.isVisible(), "MainWindow did not close")
        self.window.deleteLater()
        QApplication.processEvents()

    def _activate(self) -> None:
        from PySide6.QtTest import QTest

        self.window.show()
        self._shown = True
        self.window.activateWindow()
        if not QTest.qWaitForWindowActive(self.window, 2000):
            pytest.skip(_ACTIVATION_SKIP)
        self.focus_target.setFocus()
        QApplication.processEvents()

    def _click(self, key, modifier=None) -> None:
        from PySide6.QtCore import Qt
        from PySide6.QtTest import QTest

        QTest.keyClick(self.focus_target, key, modifier or Qt.KeyboardModifier.NoModifier)
        QApplication.processEvents()

    def test_f5_key_dispatches_f5_router_once(self):
        """F5 dispatches only to the F5 router."""
        from PySide6.QtCore import Qt

        self._activate()
        self._click(Qt.Key.Key_F5)
        self.assertEqual(self.mock_tabs.handle_f5_global.call_count, 1)
        self.assertEqual(self.mock_tabs.handle_ctrl_return_global.call_count, 0)

    def test_ctrl_return_key_dispatches_ctrl_return_router_once(self):
        """Ctrl+Return dispatches only to the Ctrl+Return router."""
        from PySide6.QtCore import Qt

        self._activate()
        self._click(Qt.Key.Key_Return, Qt.KeyboardModifier.ControlModifier)
        self.assertEqual(self.mock_tabs.handle_ctrl_return_global.call_count, 1)
        self.assertEqual(self.mock_tabs.handle_f5_global.call_count, 0)

    def test_ctrl_l_and_alt_d_reach_handle_focus_url(self):
        """Ctrl+L and Alt+D both reach handle_focus_url."""
        from PySide6.QtCore import Qt

        self._activate()
        self._click(Qt.Key.Key_L, Qt.KeyboardModifier.ControlModifier)
        ctrl_l_calls = self.mock_tabs.handle_focus_url.call_count
        self._click(Qt.Key.Key_D, Qt.KeyboardModifier.AltModifier)
        alt_d_calls = self.mock_tabs.handle_focus_url.call_count - ctrl_l_calls
        self.assertEqual(alt_d_calls, 1, "Alt+D guard regressed")
        self.assertEqual(ctrl_l_calls, 1, "Ctrl+L did not reach handle_focus_url")

    def test_no_documentation_row_binds_a_key(self):
        """No documentation row binds F5, Ctrl+Return or Ctrl+L."""
        from PySide6.QtCore import SIGNAL

        from pypost.ui.hotkeys import LABEL_PROPERTY, SECTION_PROPERTY

        bound: list[str] = []
        for action in self.window.actions():
            if not action.property(SECTION_PROPERTY):
                continue
            if action.receivers(SIGNAL("triggered(bool)")) != 0:
                continue
            if not action.shortcut().isEmpty():
                bound.append(
                    f"{action.property(SECTION_PROPERTY)}/{action.property(LABEL_PROPERTY)}"
                    f"={action.shortcut().toString()}"
                )
        self.assertEqual(bound, [], "documentation rows bind live shortcuts")

    def test_send_request_help_row_unchanged(self):
        """Request Editor 'Send Request' row text is unchanged."""
        from pypost.ui.hotkeys import collect_hotkey_rows

        sections = _rows_by_section(collect_hotkey_rows(self.window))
        self.assertEqual(sections["Request Editor"]["Send Request"], "F5 / Ctrl+Return")

    def test_other_help_rows_unchanged(self):
        """Every other Help row matches the pre-change snapshot."""
        from pypost.ui.hotkeys import collect_hotkey_rows

        rows = [
            row
            for row in collect_hotkey_rows(self.window)
            if row[0] != "Connect / Disconnect"
        ]
        self.assertEqual(rows, _EXPECTED_OTHER_HELP_ROWS)
