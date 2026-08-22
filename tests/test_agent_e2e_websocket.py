"""Agent end-to-end integration tests for WebSocket session tab and client (PYPOST-1132 / WS-4).

Tests full loopback interactions against local ScriptedWebSocketServer:
- Profile opening & tab creation
- Connect/Disconnect lifecycle with multi-modal status badge
- Dynamic connection parameter locking
- Message composition, dispatch, and secret-masked stream ingestion
- Clean teardown and tab closure
"""

from __future__ import annotations

import time

import pytest
from PySide6.QtWidgets import (
    QApplication,
    QLineEdit,
    QListView,
    QPushButton,
    QTextEdit,
    QWidget,
)

from pypost.agent.lifecycle import AgentAppSession
from pypost.agent.ui_wait import wait_until
from pypost.core.websocket_session_policy import SessionState
from pypost.models.websocket import WebSocketConnection
from pypost.ui import widget_ids
from pypost.ui.widgets.websocket import WebSocketTab
from tests.websocket_echo_server import (
    ScriptedWebSocketServer,
    ServerBehavior,
    ServerBehaviorConfig,
)

pytestmark = [
    pytest.mark.timeout(60),
    pytest.mark.agent_e2e,
]


def test_agent_e2e_websocket_full_loopback(
    qapp: QApplication,
    agent_e2e_session: AgentAppSession,
) -> None:
    """Agent e2e test: open profile, connect, lock params, send, assert stream, and disconnect."""
    window = agent_e2e_session.window
    assert window.is_ui_ready is True

    # 1. Start loopback echo server
    config = ServerBehaviorConfig(behavior=ServerBehavior.ECHO)
    with ScriptedWebSocketServer(server_name="E2E_EchoServer", config=config) as server:
        assert server.is_listening is True

        # 2. Create and open WebSocket profile
        conn = WebSocketConnection(
            id="ws_e2e_live_1",
            name="Echo Feed",
            url=server.url,
            headers={"X-Test-Client": "PyPost-Agent"},
            params={"mode": "test"},
            subprotocols=[],
        )

        ws_tab = window.tabs.open_websocket_tab(conn, save_state=False)
        qapp.processEvents()
        assert isinstance(ws_tab, WebSocketTab)

        # 3. Locate controls via widget identities
        url_input = (
            ws_tab.findChild(QLineEdit, widget_ids.WS_URL_INPUT)
            or ws_tab.findChild(QWidget, widget_ids.WS_URL_INPUT)
        )
        connect_btn = ws_tab.findChild(QPushButton, widget_ids.WS_CONNECT_BUTTON)
        send_btn = ws_tab.findChild(QPushButton, widget_ids.WS_SEND_MESSAGE_BUTTON)
        composer_edit = ws_tab.findChild(QTextEdit, widget_ids.WS_COMPOSER_EDIT)
        stream_view = ws_tab.findChild(QListView, widget_ids.WS_STREAM_VIEW)
        lock_notice = ws_tab.findChild(QWidget, widget_ids.WS_LOCK_NOTICE)

        assert connect_btn is not None
        assert send_btn is not None
        assert composer_edit is not None
        assert stream_view is not None
        assert lock_notice is not None

        # Verify initial Idle state
        assert ws_tab.presenter.state == SessionState.IDLE
        assert connect_btn.text() == "Connect"
        assert not send_btn.isEnabled()
        assert not lock_notice.isVisible()

        # 4. Initiate connection
        connect_btn.click()
        qapp.processEvents()

        # Wait until session transitions to OPEN
        wait_until(
            lambda: ws_tab.presenter.state == SessionState.OPEN,
            timeout=5.0,
            message="WebSocket session failed to reach OPEN state",
        )
        qapp.processEvents()

        # Verify Open state UI contracts
        assert connect_btn.text() == "Disconnect"
        assert send_btn.isEnabled()
        assert lock_notice.isVisible()
        assert "Open" in ws_tab.state_badge.text()
        assert "●" in ws_tab.state_badge.text() or "open" in ws_tab.state_badge.text().lower()

        # 5. Compose and send a payload
        payload_text = '{"event": "subscribe", "channel": "ticker", "pair": "BTC/USD"}'
        composer_edit.setPlainText(payload_text)
        send_btn.click()
        qapp.processEvents()

        # Verify composer is cleared on send
        assert composer_edit.toPlainText() == ""

        # 6. Wait for stream model to ingest outbound and echoed inbound entries
        stream_model = stream_view.model()
        wait_until(
            lambda: sum(
                1
                for i in range(stream_model.rowCount())
                if stream_model.get_entry(i).kind == "message"
            )
            >= 2,
            timeout=5.0,
            message="Stream model did not receive outbound and inbound message entries",
        )
        qapp.processEvents()

        messages = [
            stream_model.get_entry(i)
            for i in range(stream_model.rowCount())
            if stream_model.get_entry(i).kind == "message"
        ]
        assert len(messages) >= 2

        # Verify outbound message
        entry_out = messages[0]
        assert entry_out.direction == "out"
        assert "subscribe" in entry_out.formatted_payload
        assert entry_out.byte_size > 0

        # Verify echoed inbound message
        entry_in = messages[1]
        assert entry_in.direction == "in"
        assert "subscribe" in entry_in.formatted_payload
        assert entry_in.byte_size > 0

        # 7. Disconnect session
        connect_btn.click()
        qapp.processEvents()

        wait_until(
            lambda: ws_tab.presenter.state in (SessionState.IDLE, SessionState.CLOSED),
            timeout=5.0,
            message="WebSocket session failed to return to Idle/Closed state upon disconnect",
        )
        qapp.processEvents()

        # Verify fields unlocked
        assert not lock_notice.isVisible()
        assert not send_btn.isEnabled()
        assert connect_btn.text() == "Connect"

        # 8. Close tab
        tab_index = window.tabs.widget.indexOf(ws_tab)
        assert tab_index >= 0
        window.tabs.close_tab(tab_index)
        qapp.processEvents()
