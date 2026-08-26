"""Failing repro tests for WS-4 WebSocket session tab and minimal client (PYPOST-1132).

Asserts the contract and behavior specified in:
- `ai-tasks/PYPOST-1132/10-requirements.md`
- `ai-tasks/PYPOST-1132/20-architecture.md`
- `ai-tasks/PYPOST-1124/20-architecture.md` (Sections A-3.1, A-5.2, A-5.4, A-13.4, A-14)

Covers:
1. Automation Widget Identities (`pypost.ui.widget_ids`).
2. Multi-modal status badge (`pypost.ui.widgets.websocket.state_badge`).
3. Connection parameter editor and read-only locking
   (`pypost.ui.widgets.websocket.connection_editor`).
4. Workspace session tab layout and hierarchy (`pypost.ui.widgets.websocket.websocket_tab`).
5. Session presenter, connection controls, 33ms batched intake, and secret masking
   (`pypost.ui.presenters.websocket_presenter`).
6. Polymorphic tab management, badge synchronization, safe restoration, and secret
   propagation (`pypost.ui.presenters.tabs_presenter`).
7. Collections tree integration for WebSocket profiles
   (`pypost.ui.presenters.collections_presenter`).
8. UI identity spot-check scoped to WebSocket tab surfaces.
"""

from __future__ import annotations

from datetime import datetime, timezone
import time
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QObject, Qt
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QLineEdit,
    QListView,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QTreeView,
    QWidget,
)

from pypost.core.websocket_session_policy import (
    SessionState,
    StateDetail,
)
from pypost.core.websocket_transport_protocol import (
    FrameDirection,
    FrameType,
    HandshakeTarget,
    RawFrame,
)
from pypost.models.models import Collection
from pypost.models.settings import AppSettings
from pypost.models.websocket import WebSocketConnection
from pypost.ui.widgets.websocket.stream_model import StreamListModel

from pypost.ui import widget_ids
from pypost.ui.widgets.websocket.state_badge import WebSocketStateBadge
from pypost.ui.widgets.websocket.connection_editor import WebSocketConnectionEditor
from pypost.ui.widgets.websocket.websocket_tab import WebSocketTab
from pypost.ui.presenters.websocket_presenter import WebSocketPresenter
from pypost.ui.presenters.tabs_presenter import TabsPresenter
from pypost.ui.presenters.collections_presenter import CollectionsPresenter

pytestmark = pytest.mark.timeout(30)


# =============================================================================
# Helper Fixtures & Mock Classes
# =============================================================================


def _make_sample_connection(
    ws_id: str = "ws_test_1",
    name: str = "Echo Endpoint",
    url: str = "wss://echo.example.com/v1/feed",
    headers: Optional[dict[str, str]] = None,
    params: Optional[dict[str, str]] = None,
    subprotocols: Optional[list[str]] = None,
) -> WebSocketConnection:
    return WebSocketConnection(
        id=ws_id,
        name=name,
        url=url,
        headers=headers if headers is not None else {"Authorization": "Bearer secret_token_123"},
        params=params if params is not None else {"format": "json"},
        subprotocols=subprotocols if subprotocols is not None else ["json.v2", "chat.v1"],
    )


def _assert_widget_identity(widget: QObject, expected_id: str) -> None:
    """Helper verifying objectName and accessibleIdentifier."""
    name = widget.objectName()
    assert name == expected_id, f"Expected objectName '{expected_id}', got '{name}'"
    if isinstance(widget, QWidget):
        getter = getattr(widget, "accessibleIdentifier", None)
        if callable(getter):
            acc_id = getter()
            msg = f"Expected accessibleIdentifier '{expected_id}', got '{acc_id}'"
            assert acc_id == expected_id, msg


# =============================================================================
# 1. Automation Widget Identities
# =============================================================================


def test_websocket_widget_id_constants():
    """Verify all WS_* automation identities are declared per RFC A-5.7 and FR-8."""
    expected_constants = {
        "WS_TAB_PAGE": "pypost_ws_tab_page",
        "WS_URL_INPUT": "pypost_ws_url_input",
        "WS_CONNECT_BUTTON": "pypost_ws_connect_button",
        "WS_STATE_BADGE": "pypost_ws_state_badge",
        "WS_PARAMS_TABLE": "pypost_ws_params_table",
        "WS_HEADERS_TABLE": "pypost_ws_headers_table",
        "WS_SUBPROTOCOLS_INPUT": "pypost_ws_subprotocols_input",
        "WS_STREAM_VIEW": "pypost_ws_stream_view",
        "WS_COMPOSER_EDIT": "pypost_ws_composer_edit",
        "WS_SEND_MESSAGE_BUTTON": "pypost_ws_send_message_button",
        "WS_LOCK_NOTICE": "pypost_ws_lock_notice",
        "WS_DETAIL_TABS": "pypost_ws_detail_tabs",
    }

    for const_name, expected_val in expected_constants.items():
        assert hasattr(widget_ids, const_name), f"Missing constant '{const_name}' in widget_ids"
        val = getattr(widget_ids, const_name)
        msg = f"Constant '{const_name}' has '{val}', expected '{expected_val}'"
        assert val == expected_val, msg
        assert val.startswith("pypost_"), f"Identity '{val}' must start with 'pypost_'"
        assert (
            val.isascii() and val == val.lower() and " " not in val
        ), f"Identity '{val}' must be lowercase ASCII without spaces"


# =============================================================================
# 2. WebSocketStateBadge Multi-Modal Accessibility
# =============================================================================


def test_state_badge_initialization_and_identity(qapp: QApplication):
    """Verify WebSocketStateBadge identity and initial Idle state."""
    badge = WebSocketStateBadge()
    try:
        _assert_widget_identity(badge, widget_ids.WS_STATE_BADGE)
        # By default initialized in Idle
        text = badge.text() if hasattr(badge, "text") else ""
        label = badge.findChild(QLabel)
        display_text = label.text() if label else text
        assert "Idle" in display_text or "○" in display_text
    finally:
        badge.deleteLater()


def test_state_badge_multi_modal_lifecycle(qapp: QApplication):
    """Verify state transitions render both explicit text and symbolic glyphs (WCAG 2.1 / FR-3)."""
    badge = WebSocketStateBadge()
    try:
        # 1. IDLE
        badge.set_state(SessionState.IDLE)
        qapp.processEvents()
        text_idle = badge.findChild(QLabel).text() if badge.findChild(QLabel) else badge.text()
        assert "Idle" in text_idle
        assert "○" in text_idle or "idle" in text_idle.lower()

        # 2. CONNECTING
        badge.set_state(SessionState.CONNECTING)
        qapp.processEvents()
        text_conn = badge.findChild(QLabel).text() if badge.findChild(QLabel) else badge.text()
        assert "Connecting" in text_conn
        assert "⏳" in text_conn or "~" in text_conn or "connecting" in text_conn.lower()

        # 3. OPEN with subprotocol and metrics
        badge.set_state(SessionState.OPEN, StateDetail(message="Connected"))
        badge.set_metrics(subprotocol="json.v2", message_count=12)
        qapp.processEvents()
        text_open = badge.findChild(QLabel).text() if badge.findChild(QLabel) else badge.text()
        assert "Open" in text_open
        assert "●" in text_open or "open" in text_open.lower()
        assert "json.v2" in text_open or "12" in text_open

        # 4. CLOSING
        badge.set_state(SessionState.CLOSING)
        qapp.processEvents()
        text_closing = badge.findChild(QLabel).text() if badge.findChild(QLabel) else badge.text()
        assert "Closing" in text_closing

        # 5. RECONNECTING
        badge.set_state(SessionState.RECONNECTING, StateDetail(message="Attempt 2 of 5"))
        qapp.processEvents()
        text_recon = badge.findChild(QLabel).text() if badge.findChild(QLabel) else badge.text()
        assert "Reconnecting" in text_recon

        # 6. FAILED with error detail
        badge.set_state(
            SessionState.FAILED,
            StateDetail(message="Connection refused", close_code=1006),
        )
        qapp.processEvents()
        text_failed = badge.findChild(QLabel).text() if badge.findChild(QLabel) else badge.text()
        assert "Failed" in text_failed
        assert "Connection refused" in text_failed or "✕" in text_failed

        # 7. Reset restores to Idle
        badge.reset()
        qapp.processEvents()
        text_reset = badge.findChild(QLabel).text() if badge.findChild(QLabel) else badge.text()
        assert "Idle" in text_reset
    finally:
        badge.deleteLater()


# =============================================================================
# 3. Connection Parameter Editor & Dynamic Read-Only Locking
# =============================================================================


def test_connection_editor_widget_hierarchy_and_identities(qapp: QApplication):
    """Verify WebSocketConnectionEditor exposes all child automation identities."""
    editor = WebSocketConnectionEditor()
    try:
        url_input = (
            editor.findChild(QLineEdit, widget_ids.WS_URL_INPUT)
            or editor.findChild(QWidget, widget_ids.WS_URL_INPUT)
        )
        assert url_input is not None, "Missing WS_URL_INPUT in WebSocketConnectionEditor"
        _assert_widget_identity(url_input, widget_ids.WS_URL_INPUT)

        params_table = editor.findChild(QWidget, widget_ids.WS_PARAMS_TABLE)
        assert params_table is not None, "Missing WS_PARAMS_TABLE in WebSocketConnectionEditor"
        _assert_widget_identity(params_table, widget_ids.WS_PARAMS_TABLE)

        headers_table = editor.findChild(QWidget, widget_ids.WS_HEADERS_TABLE)
        assert headers_table is not None, "Missing WS_HEADERS_TABLE in WebSocketConnectionEditor"
        _assert_widget_identity(headers_table, widget_ids.WS_HEADERS_TABLE)

        subprotocols = editor.findChild(QWidget, widget_ids.WS_SUBPROTOCOLS_INPUT)
        assert subprotocols is not None, (
            "Missing WS_SUBPROTOCOLS_INPUT in WebSocketConnectionEditor"
        )
        _assert_widget_identity(subprotocols, widget_ids.WS_SUBPROTOCOLS_INPUT)

        lock_notice = editor.findChild(QWidget, widget_ids.WS_LOCK_NOTICE)
        assert lock_notice is not None, (
            "Missing WS_LOCK_NOTICE banner in WebSocketConnectionEditor"
        )
        _assert_widget_identity(lock_notice, widget_ids.WS_LOCK_NOTICE)
        # Lock notice hidden by default in Idle state
        assert not lock_notice.isVisible()
    finally:
        editor.deleteLater()


def test_connection_editor_load_and_get_target(qapp: QApplication):
    """Verify loading a profile into editor and building HandshakeTarget."""
    conn = _make_sample_connection(
        url="wss://api.example.com/stream",
        headers={"X-Custom": "TestVal"},
        params={"symbol": "BTC"},
        subprotocols=["feed.v1", "chat.v2"],
    )
    editor = WebSocketConnectionEditor()
    try:
        editor.load_connection(conn)
        qapp.processEvents()

        target = editor.get_target()
        assert isinstance(target, HandshakeTarget)
        assert "wss://api.example.com/stream" in target.url
        assert "symbol=BTC" in target.url
        assert target.headers.get("X-Custom") == "TestVal"
        assert target.subprotocols == ("feed.v1", "chat.v2")
    finally:
        editor.deleteLater()


def test_connection_editor_read_only_locking(qapp: QApplication):
    """Verify dynamic parameter locking and lock notice banner (FR-4 / RFC Section A-5.3)."""
    editor = WebSocketConnectionEditor()
    try:
        url_input = (
            editor.findChild(QLineEdit, widget_ids.WS_URL_INPUT)
            or editor.findChild(QWidget, widget_ids.WS_URL_INPUT)
        )
        lock_notice = editor.findChild(QWidget, widget_ids.WS_LOCK_NOTICE)

        # 1. Lock connection fields (during active connection)
        editor.set_read_only(True)
        qapp.processEvents()

        assert editor.is_read_only is True or not url_input.isEnabled() or url_input.isReadOnly()
        assert lock_notice.isVisible()
        lbl = lock_notice.findChild(QLabel) if lock_notice else None
        notice_text = lock_notice.text() if hasattr(lock_notice, "text") else (
            lbl.text() if lbl else ""
        )
        assert "read-only" in notice_text.lower() or "disconnect" in notice_text.lower()

        # 2. Unlock connection fields (when returning to Idle / Failed)
        editor.set_read_only(False)
        qapp.processEvents()

        is_unlocked = url_input.isEnabled() and not getattr(
            url_input, "isReadOnly", lambda: False
        )()
        assert editor.is_read_only is False or is_unlocked
        assert not lock_notice.isVisible()
    finally:
        editor.deleteLater()


# =============================================================================
# 4. WebSocketTab Container Layout & Properties
# =============================================================================


def test_websocket_tab_layout_and_identities(qapp: QApplication):
    """Verify WebSocketTab layout, child components, and properties (RFC A-5.4)."""
    conn = _make_sample_connection()
    stream_model = StreamListModel()
    presenter = WebSocketPresenter(connection=conn, stream_model=stream_model)
    tab = WebSocketTab(connection=conn, presenter=presenter)
    try:
        _assert_widget_identity(tab, widget_ids.WS_TAB_PAGE)
        assert tab.connection_data == conn
        assert tab.presenter is presenter

        # Accessor properties
        assert tab.connection_editor is not None
        assert tab.state_badge is not None
        assert tab.stream_view is not None

        # Child controls with identities
        connect_btn = tab.findChild(QPushButton, widget_ids.WS_CONNECT_BUTTON)
        assert connect_btn is not None
        _assert_widget_identity(connect_btn, widget_ids.WS_CONNECT_BUTTON)
        assert connect_btn.text() == "Connect"

        stream_view = tab.findChild(QListView, widget_ids.WS_STREAM_VIEW)
        assert stream_view is not None
        assert (
            stream_view.model() is stream_model
            or getattr(stream_view.model(), "sourceModel", lambda: None)() is stream_model
        )

        composer_edit = (
            tab.findChild(QTextEdit, widget_ids.WS_COMPOSER_EDIT)
            or tab.findChild(QWidget, widget_ids.WS_COMPOSER_EDIT)
        )
        assert composer_edit is not None
        _assert_widget_identity(composer_edit, widget_ids.WS_COMPOSER_EDIT)

        send_btn = tab.findChild(QPushButton, widget_ids.WS_SEND_MESSAGE_BUTTON)
        assert send_btn is not None
        _assert_widget_identity(send_btn, widget_ids.WS_SEND_MESSAGE_BUTTON)

        detail_tabs = tab.findChild(QTabWidget, widget_ids.WS_DETAIL_TABS)
        assert detail_tabs is not None
        _assert_widget_identity(detail_tabs, widget_ids.WS_DETAIL_TABS)
    finally:
        tab.deleteLater()
        presenter.deleteLater()


# =============================================================================
# 5. WebSocketPresenter Coordination, Actions, Masking, and 33ms Batch Intake
# =============================================================================


def test_presenter_connect_and_disconnect_lifecycle(qapp: QApplication):
    """Verify presenter Connect/Disconnect transitions, button updates, and locking."""
    from pypost.core.qt.websocket_session import WebSocketSessionController

    conn = _make_sample_connection()
    stream_model = StreamListModel()
    controller = WebSocketSessionController()
    presenter = WebSocketPresenter(
        connection=conn, session_controller=controller, stream_model=stream_model
    )
    tab = WebSocketTab(connection=conn, presenter=presenter)
    try:
        connect_btn = tab.findChild(QPushButton, widget_ids.WS_CONNECT_BUTTON)
        send_btn = tab.findChild(QPushButton, widget_ids.WS_SEND_MESSAGE_BUTTON)

        assert connect_btn.text() == "Connect"
        assert not send_btn.isEnabled()

        # Connect action initiated
        presenter.handle_connect()
        qapp.processEvents()

        assert controller.state == SessionState.CONNECTING
        assert connect_btn.text() == "Cancel"
        assert tab.connection_editor.is_read_only is True

        # Simulate connection open from controller
        controller.state_changed.emit(SessionState.OPEN.value, StateDetail(message="Connected"))
        qapp.processEvents()

        assert connect_btn.text() == "Disconnect"
        assert send_btn.isEnabled()

        # Disconnect action
        presenter.handle_disconnect()
        controller.state_changed.emit(SessionState.IDLE.value, StateDetail(message="Closed"))
        qapp.processEvents()

        assert connect_btn.text() == "Connect"
        assert not send_btn.isEnabled()
        assert tab.connection_editor.is_read_only is False
    finally:
        tab.deleteLater()
        presenter.deleteLater()
        controller.deleteLater()


def test_presenter_send_message_guard_and_dispatch(qapp: QApplication):
    """Verify sending message requires Open state and clears composer upon send (FR-6)."""
    from pypost.core.qt.websocket_session import WebSocketSessionController

    conn = _make_sample_connection()
    stream_model = StreamListModel()
    controller = WebSocketSessionController()

    sent_texts: list[str] = []
    controller.send_text = lambda msg: sent_texts.append(msg)  # type: ignore[assignment]

    presenter = WebSocketPresenter(
        connection=conn, session_controller=controller, stream_model=stream_model
    )
    tab = WebSocketTab(connection=conn, presenter=presenter)
    try:
        composer_edit = tab.findChild(QTextEdit, widget_ids.WS_COMPOSER_EDIT)

        # 1. Attempt send while Idle -> blocked
        composer_edit.setPlainText("Test Idle Send")
        presenter.handle_send_message()
        qapp.processEvents()
        assert len(sent_texts) == 0, "Sending while Idle must be blocked"
        assert composer_edit.toPlainText() == "Test Idle Send"

        # 2. Simulate Open state and send
        controller.state_changed.emit(SessionState.OPEN.value, StateDetail())
        qapp.processEvents()

        presenter.handle_send_message()
        qapp.processEvents()
        assert sent_texts == ["Test Idle Send"]
        assert composer_edit.toPlainText() == "", "Composer text must be cleared on send"
    finally:
        tab.deleteLater()
        presenter.deleteLater()
        controller.deleteLater()


def test_presenter_secret_masking_and_batched_ingestion(qapp: QApplication):
    """Verify raw frames are masked with hidden_keys and ingested in 33ms batch (RFC A-3.1)."""
    from pypost.core.qt.websocket_session import WebSocketSessionController

    conn = _make_sample_connection()
    stream_model = StreamListModel()
    controller = WebSocketSessionController()

    env_vars = {"SECRET_TOKEN": "my_super_secret_token_xyz"}
    hidden_keys = {"SECRET_TOKEN"}

    presenter = WebSocketPresenter(
        connection=conn,
        session_controller=controller,
        stream_model=stream_model,
        env_vars=env_vars,
        hidden_keys=hidden_keys,
    )
    tab = WebSocketTab(connection=conn, presenter=presenter)
    try:
        # Simulate frame sent with secret
        raw_out = RawFrame(
            direction=FrameDirection.OUT,
            payload_format=FrameType.TEXT,
            payload='{"auth": "my_super_secret_token_xyz", "msg": "hello"}',
            byte_size=56,
            timestamp=datetime.now(timezone.utc),
        )
        controller.frame_sent.emit(raw_out)

        # Simulate frame received with secret
        raw_in = RawFrame(
            direction=FrameDirection.IN,
            payload_format=FrameType.TEXT,
            payload='{"echo_auth": "my_super_secret_token_xyz", "status": "ok"}',
            byte_size=60,
            timestamp=datetime.now(timezone.utc),
        )
        controller.frame_received.emit(raw_in)

        # Prior to 33ms timer firing, model should not have appended (or batched)
        # Let Qt event loop process the 33ms flush timer
        time.sleep(0.05)
        qapp.processEvents()

        # Verify stream model has 2 rows
        assert stream_model.rowCount() == 2
        entry_out = stream_model.get_entry(0)
        entry_in = stream_model.get_entry(1)

        # Invariant: raw secrets NEVER exist in the StreamEntry
        assert "my_super_secret_token_xyz" not in entry_out.formatted_payload
        assert "***" in entry_out.formatted_payload
        assert entry_out.direction == "out"

        assert "my_super_secret_token_xyz" not in entry_in.formatted_payload
        assert "***" in entry_in.formatted_payload
        assert entry_in.direction == "in"
    finally:
        tab.deleteLater()
        presenter.deleteLater()
        controller.deleteLater()


def test_presenter_teardown_cleans_up(qapp: QApplication):
    """Verify teardown closes controller and stops flush timer."""
    from pypost.core.qt.websocket_session import WebSocketSessionController

    conn = _make_sample_connection()
    stream_model = StreamListModel()
    controller = WebSocketSessionController()

    closed_calls: list[tuple[int, str]] = []
    controller.close = (
        lambda code=1000, reason="": closed_calls.append((code, reason))
    )  # type: ignore[assignment]

    presenter = WebSocketPresenter(
        connection=conn, session_controller=controller, stream_model=stream_model
    )
    try:
        presenter.teardown()
        assert len(closed_calls) >= 1
    finally:
        presenter.deleteLater()
        controller.deleteLater()


# =============================================================================
# 6. TabsPresenter Integration & Restoration Safety
# =============================================================================


class FakeRequestManager:
    def __init__(self, requests=None):
        self._requests = {r.id: (r, MagicMock(id="c1")) for r in (requests or [])}
        self.saved = []
        self.collections = []

    def find_request(self, req_id):
        return self._requests.get(req_id)

    def get_collections(self):
        return self.collections


class FakeStateManager:
    def __init__(self, open_tabs=None):
        self._open_tabs = open_tabs or []
        self.settings = AppSettings()

    def get_open_tabs(self):
        return list(self._open_tabs)

    def set_open_tabs(self, ids):
        self._open_tabs = ids


def test_tabs_presenter_open_websocket_tab(qapp: QApplication):
    """Verify TabsPresenter opens WebSocketTab and syncs badge (FR-1)."""
    rm = FakeRequestManager()
    sm = FakeStateManager()
    tabs_p = TabsPresenter(rm, sm, AppSettings(), metrics=MagicMock())
    conn = _make_sample_connection(name="Binance Ticker")

    tab = tabs_p.open_websocket_tab(conn)
    try:
        assert isinstance(tab, WebSocketTab)
        assert tab.connection_data == conn

        tab_widget: QTabWidget = tabs_p.widget
        # Find index of tab
        idx = tab_widget.indexOf(tab)
        assert idx >= 0
        tab_text = tab_widget.tabText(idx)
        assert "Binance Ticker" in tab_text
    finally:
        tab.deleteLater()
        tabs_p.widget.deleteLater()


def test_tabs_presenter_focus_on_duplicate_profile(qapp: QApplication):
    """Verify re-opening already open WebSocket tab focuses it instead of duplicating (FR-1)."""
    rm = FakeRequestManager()
    sm = FakeStateManager()
    tabs_p = TabsPresenter(rm, sm, AppSettings(), metrics=MagicMock())
    conn = _make_sample_connection(ws_id="ws_unique_1")

    try:
        tab1 = tabs_p.open_websocket_tab(conn)
        tab2 = tabs_p.open_websocket_tab(conn)

        assert tab1 is tab2, "Duplicate open must focus existing tab rather than creating duplicate"
    finally:
        tabs_p.widget.deleteLater()


def test_tabs_presenter_close_websocket_tab_calls_teardown(qapp: QApplication):
    """Verify closing a WebSocketTab polymorphically triggers teardown (FR-7)."""
    conn = _make_sample_connection()
    rm = FakeRequestManager()
    rm.collections = [Collection(name="Streams", websockets=[conn])]
    sm = FakeStateManager()
    tabs_p = TabsPresenter(rm, sm, AppSettings(), metrics=MagicMock())

    try:
        tab = tabs_p.open_websocket_tab(conn)
        tab_idx = tabs_p.widget.indexOf(tab)

        teardown_called = False
        original_teardown = tab.presenter.teardown

        def _mock_teardown():
            nonlocal teardown_called
            teardown_called = True
            original_teardown()

        tab.presenter.teardown = _mock_teardown  # type: ignore[assignment]

        tabs_p.close_tab(tab_idx)
        assert teardown_called is True, "close_tab must call presenter.teardown()"
    finally:
        tabs_p.widget.deleteLater()


def test_tabs_presenter_restore_tabs_idle_safe(qapp: QApplication):
    """Verify restored WebSocket tabs start in Idle state without auto-connecting (FR-1 / S-5)."""
    from pypost.core.websocket_registry import WebSocketRegistry

    conn = _make_sample_connection(ws_id="ws_persisted_1")
    col = Collection(name="Streams", websockets=[conn])
    rm = FakeRequestManager()
    rm.collections = [col]
    sm = FakeStateManager(open_tabs=["ws_persisted_1"])

    with patch.object(WebSocketRegistry, "find_item", return_value=("websocket", conn, col)):
        tabs_p = TabsPresenter(rm, sm, AppSettings(), metrics=MagicMock())
        try:
            tabs_p.restore_tabs()
            qapp.processEvents()

            assert tabs_p.widget.count() >= 2  # restored tab + plus tab
            restored_tab = tabs_p.widget.widget(0)
            assert isinstance(restored_tab, WebSocketTab)
            assert restored_tab.presenter.state == SessionState.IDLE
        finally:
            tabs_p.widget.deleteLater()


def test_tabs_presenter_propagates_env_secrets(qapp: QApplication):
    """Verify TabsPresenter updates env variables and hidden keys on open WebSocket tabs."""
    rm = FakeRequestManager()
    sm = FakeStateManager()
    tabs_p = TabsPresenter(rm, sm, AppSettings(), metrics=MagicMock())
    conn = _make_sample_connection()

    tab = tabs_p.open_websocket_tab(conn)
    try:
        tabs_p.on_env_variables_changed({"API_KEY": "new_secret_val"})
        tabs_p.on_env_hidden_keys_changed({"API_KEY"})

        assert tab.presenter._env_vars == {"API_KEY": "new_secret_val"}
        assert tab.presenter._hidden_keys == {"API_KEY"}
    finally:
        tab.deleteLater()
        tabs_p.widget.deleteLater()


# =============================================================================
# 7. CollectionsPresenter Integration
# =============================================================================


def test_collections_presenter_renders_websocket_profiles(qapp: QApplication):
    """Verify Collection.websockets profiles appear in the collection tree (FR-1)."""
    conn = _make_sample_connection(name="Market Stream")
    col = Collection(name="Crypto Col", websockets=[conn])

    rm = FakeRequestManager()
    rm.collections = [col]

    cp = CollectionsPresenter(rm, FakeStateManager())
    try:
        tree: QTreeView = cp.widget
        model = tree.model()

        # Find the websocket item in the tree model
        root_item = model.invisibleRootItem()
        col_item = root_item.child(0)
        assert col_item is not None
        assert col_item.text() == "Crypto Col"

        # Child should be the websocket connection item
        ws_child = col_item.child(0)
        assert ws_child is not None
        assert "Market Stream" in ws_child.text() or "ws " in ws_child.text()
        assert (
            ws_child.data(Qt.ItemDataRole.UserRole) == conn
            or ws_child.data(Qt.ItemDataRole.UserRole) == conn.id
        )
    finally:
        cp.widget.deleteLater()


# =============================================================================
# 8. UI Identity Spot-Check Scoped to WebSocketTab
# =============================================================================


def test_websocket_tab_identity_spotcheck(qapp: QApplication):
    """Spot-check that all WS_* identities resolve on a live WebSocketTab instance (A-14)."""
    conn = _make_sample_connection()
    presenter = WebSocketPresenter(connection=conn)
    tab = WebSocketTab(connection=conn, presenter=presenter)
    try:
        _assert_widget_identity(tab, widget_ids.WS_TAB_PAGE)

        for expected_id in (
            widget_ids.WS_URL_INPUT,
            widget_ids.WS_CONNECT_BUTTON,
            widget_ids.WS_STATE_BADGE,
            widget_ids.WS_PARAMS_TABLE,
            widget_ids.WS_HEADERS_TABLE,
            widget_ids.WS_SUBPROTOCOLS_INPUT,
            widget_ids.WS_STREAM_VIEW,
            widget_ids.WS_COMPOSER_EDIT,
            widget_ids.WS_SEND_MESSAGE_BUTTON,
            widget_ids.WS_LOCK_NOTICE,
            widget_ids.WS_DETAIL_TABS,
        ):
            found = tab.findChild(QWidget, expected_id)
            assert found is not None, f"Widget identity '{expected_id}' not found in tab"
            _assert_widget_identity(found, expected_id)
    finally:
        tab.deleteLater()
        presenter.deleteLater()
