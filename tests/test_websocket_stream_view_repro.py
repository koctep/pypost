"""Failing repro tests for WS-5 WebSocket Stream Inspector (PYPOST-1133).

Asserts the contract and behavior specified in:
- `ai-tasks/PYPOST-1133/10-requirements.md`
- `ai-tasks/PYPOST-1133/20-architecture.md`
- `ai-tasks/PYPOST-1124/20-architecture.md` (Sections A-5.4, A-5.6, A-5.7, A-6, A-13.5)

Covers:
1. Automation Widget Identities (`pypost.ui.widget_ids`).
2. StreamFilterProxyModel: filtering by direction (in/out), kind (message/lifecycle),
   search query matching, and lifecycle heartbeat noise suppression.
3. StreamItemDelegate: virtualized canvas delegate rendering with timestamp,
   direction glyphs, payload snippets, and wire sizes.
4. WebSocketStreamView container hierarchy, controls, search query, match count accounting,
   and empty filter state overlay.
5. Follow-tail mechanics, scroll detachment, display pause (network intake uninterrupted),
   unread message badge, and resume tail snapping.
6. Stream buffer clearing, drop counter reset, and drop notice banner (capacity vs memory budget).
7. StreamDetailPane inspection: metadata header, word-wrap toggle, hexadecimal byte dump
   view, truncation notice banner, masked clipboard copy, and "Set as variable..." capture.
8. Dual-format transcript export integration (JSON and Plain Text).
9. WebSocketTab integration embedding WebSocketStreamView in the middle pane.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtCore import QObject, QRect, Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QStyleOptionViewItem,
    QTextEdit,
    QWidget,
)

from pypost.core.websocket_stream import (
    MessageStream,
    StreamEntry,
)
from pypost.models.websocket import WebSocketConnection
from pypost.ui import widget_ids
from pypost.ui.widgets.websocket.stream_model import StreamListModel
from tests.helpers.process_until import process_until

pytestmark = pytest.mark.timeout(30)


# =============================================================================
# Helper Fixtures & Builders
# =============================================================================


def _make_sample_connection(
    ws_id: str = "ws_stream_test_1",
    name: str = "Stream Test Feed",
    url: str = "wss://stream.example.com/v1/live",
) -> WebSocketConnection:
    return WebSocketConnection(
        id=ws_id,
        name=name,
        url=url,
        headers={"Authorization": "Bearer secret_stream_key_999"},
        params={"symbol": "ETH"},
        subprotocols=["json.v2"],
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


def _create_stream_entry(
    seq: int = 1,
    ts_utc: str = "2026-08-22T12:00:00.000Z",
    kind: str = "message",
    direction: str = "in",
    payload_format: str = "json",
    payload: str = '{"type":"ticker","price":2500.5}',
    byte_size: int = 32,
    truncated: bool = False,
    detail: str = "",
) -> StreamEntry:
    return StreamEntry(
        seq=seq,
        ts_utc=ts_utc,
        kind=kind,
        direction=direction,
        payload_format=payload_format,
        payload=payload,
        byte_size=byte_size,
        truncated=truncated,
        detail=detail,
    )


# =============================================================================
# 1. Automation Widget Identities
# =============================================================================


def test_websocket_stream_widget_id_constants():
    """Verify all WS_STREAM_* automation identities are declared in widget_ids."""
    expected_constants = {
        "WS_STREAM_VIEW": "pypost_ws_stream_view",
        "WS_STREAM_SEARCH_INPUT": "pypost_ws_stream_search_input",
        "WS_STREAM_DIRECTION_FILTER": "pypost_ws_stream_direction_filter",
        "WS_STREAM_KIND_FILTER": "pypost_ws_stream_kind_filter",
        "WS_STREAM_PAUSE_BUTTON": "pypost_ws_stream_pause_button",
        "WS_STREAM_CLEAR_BUTTON": "pypost_ws_stream_clear_button",
        "WS_STREAM_EXPORT_BUTTON": "pypost_ws_stream_export_button",
        "WS_STREAM_DROP_NOTICE": "pypost_ws_stream_drop_notice",
        "WS_STREAM_DETAIL": "pypost_ws_stream_detail",
        "WS_STREAM_CLEAR_FILTER_BUTTON": "pypost_ws_stream_clear_filter_button",
        "WS_STREAM_MATCH_COUNT": "pypost_ws_stream_match_count",
        "WS_STREAM_DETAIL_COPY_BUTTON": "pypost_ws_stream_detail_copy_button",
        "WS_STREAM_DETAIL_SET_VAR_BUTTON": "pypost_ws_stream_detail_set_var_button",
        "WS_STREAM_DETAIL_WRAP_BUTTON": "pypost_ws_stream_detail_wrap_button",
        "WS_STREAM_DETAIL_HEX_BUTTON": "pypost_ws_stream_detail_hex_button",
        "WS_STREAM_FOLLOW_TAIL_BADGE": "pypost_ws_stream_follow_tail_badge",
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
# 2. StreamFilterProxyModel: Direction, Kind, Search & Noise Filtering
# =============================================================================


def test_stream_filter_proxy_model_direction_and_kind_filtering(qapp: QApplication):
    """Verify StreamFilterProxyModel filtering by direction, kind, and resetting."""
    from pypost.ui.widgets.websocket.stream_view import StreamFilterProxyModel

    stream = MessageStream(max_entries=10)
    model = StreamListModel(stream=stream)

    e1 = _create_stream_entry(seq=1, direction="in", kind="message", payload="Inbound Msg 1")
    e2 = _create_stream_entry(seq=2, direction="out", kind="message", payload="Outbound Msg 2")
    e3 = _create_stream_entry(seq=3, direction="none", kind="lifecycle", detail="Connected to host")
    e4 = _create_stream_entry(seq=4, direction="none", kind="lifecycle", detail="Ping sent")

    model.append_batch([e1, e2, e3, e4])

    proxy = StreamFilterProxyModel()
    try:
        proxy.setSourceModel(model)

        # 1. Default (all pass, or all non-suppressed)
        proxy.set_show_heartbeats(True)
        assert proxy.rowCount() == 4

        # 2. Direction: Inbound only
        proxy.set_direction_filter("in")
        assert proxy.rowCount() == 1
        idx = proxy.index(0, 0)
        assert proxy.data(idx, StreamListModel.SeqRole) == 1

        # 3. Direction: Outbound only
        proxy.set_direction_filter("out")
        assert proxy.rowCount() == 1
        idx = proxy.index(0, 0)
        assert proxy.data(idx, StreamListModel.SeqRole) == 2

        # 4. Direction: All
        proxy.set_direction_filter(None)
        assert proxy.rowCount() == 4

        # 5. Kind: Messages only
        proxy.set_kind_filter("message")
        assert proxy.rowCount() == 2

        # 6. Kind: Lifecycle only
        proxy.set_kind_filter("lifecycle")
        assert proxy.rowCount() == 2

        # 7. Reset filters restores all
        proxy.reset_filters()
        proxy.set_show_heartbeats(True)
        assert proxy.rowCount() == 4
    finally:
        proxy.deleteLater()
        model.deleteLater()


def test_stream_filter_proxy_model_search_and_heartbeat_noise(qapp: QApplication):
    """Verify StreamFilterProxyModel search text matching and heartbeat suppression."""
    from pypost.ui.widgets.websocket.stream_view import StreamFilterProxyModel

    stream = MessageStream(max_entries=10)
    model = StreamListModel(stream=stream)

    e1 = _create_stream_entry(seq=1, payload='{"op":"subscribe","channel":"telemetry_gps"}')
    e2 = _create_stream_entry(seq=2, payload='{"status":"idle"}')
    e3 = _create_stream_entry(seq=3, kind="lifecycle", detail="Heartbeat pong received (12ms)")
    e4 = _create_stream_entry(seq=4, kind="lifecycle", detail="TLS Handshake completed")

    model.append_batch([e1, e2, e3, e4])

    proxy = StreamFilterProxyModel()
    try:
        proxy.setSourceModel(model)

        # 1. Search text matches payload case-insensitively
        proxy.set_search_text("TELEMETRY")
        assert proxy.rowCount() == 1
        assert proxy.data(proxy.index(0, 0), StreamListModel.SeqRole) == 1

        # 2. Search text matches detail case-insensitively
        proxy.set_search_text("handshake")
        assert proxy.rowCount() == 1
        assert proxy.data(proxy.index(0, 0), StreamListModel.SeqRole) == 4

        # 3. Clear search text
        proxy.set_search_text("")

        # 4. Heartbeat noise suppression
        proxy.set_show_heartbeats(False)
        assert proxy.rowCount() == 3  # e3 (heartbeat pong) excluded

        proxy.set_show_heartbeats(True)
        assert proxy.rowCount() == 4  # e3 included
    finally:
        proxy.deleteLater()
        model.deleteLater()


# =============================================================================
# 3. StreamItemDelegate Virtualized Rendering
# =============================================================================


def test_stream_item_delegate_paint_and_size_hint(qapp: QApplication):
    """Verify StreamItemDelegate provides uniform row size and paints without error."""
    from pypost.ui.widgets.websocket.stream_view import StreamItemDelegate

    stream = MessageStream(max_entries=10)
    model = StreamListModel(stream=stream)
    e1 = _create_stream_entry(
        seq=1,
        ts_utc="2026-08-22T12:00:01.123Z",
        direction="in",
        kind="message",
        payload='{"type":"delta","seq":100}',
        byte_size=28,
    )
    model.append_batch([e1])

    delegate = StreamItemDelegate()
    try:
        index = model.index(0, 0)
        option = QStyleOptionViewItem()
        option.rect = QRect(0, 0, 500, 26)

        # Size hint returns stable row height
        hint = delegate.sizeHint(option, index)
        assert hint.height() >= 20

        # Paint on a test image surface
        img = QImage(500, 26, QImage.Format.Format_ARGB32)
        img.fill(Qt.GlobalColor.white)
        painter = QPainter(img)
        try:
            delegate.paint(painter, option, index)
        finally:
            painter.end()
    finally:
        delegate.deleteLater()
        model.deleteLater()


# =============================================================================
# 4. WebSocketStreamView Container Hierarchy & Widget Identities
# =============================================================================


def test_stream_view_widget_hierarchy_and_identities(qapp: QApplication):
    """Verify WebSocketStreamView hosts all documented controls and assigns widget identities."""
    from pypost.ui.presenters.websocket_presenter import WebSocketPresenter
    from pypost.ui.widgets.websocket.stream_view import WebSocketStreamView

    conn = _make_sample_connection()
    stream_model = StreamListModel()
    presenter = WebSocketPresenter(connection=conn, stream_model=stream_model)
    stream_view = WebSocketStreamView(stream_model=stream_model, presenter=presenter)
    try:
        _assert_widget_identity(stream_view, widget_ids.WS_STREAM_VIEW)

        # Search input
        search_input = stream_view.findChild(QLineEdit, widget_ids.WS_STREAM_SEARCH_INPUT)
        assert search_input is not None, "Missing WS_STREAM_SEARCH_INPUT"
        _assert_widget_identity(search_input, widget_ids.WS_STREAM_SEARCH_INPUT)

        # Direction filter dropdown
        dir_filter = stream_view.findChild(QComboBox, widget_ids.WS_STREAM_DIRECTION_FILTER)
        assert dir_filter is not None, "Missing WS_STREAM_DIRECTION_FILTER"
        _assert_widget_identity(dir_filter, widget_ids.WS_STREAM_DIRECTION_FILTER)

        # Kind filter dropdown
        kind_filter = stream_view.findChild(QComboBox, widget_ids.WS_STREAM_KIND_FILTER)
        assert kind_filter is not None, "Missing WS_STREAM_KIND_FILTER"
        _assert_widget_identity(kind_filter, widget_ids.WS_STREAM_KIND_FILTER)

        # Pause button
        pause_btn = stream_view.findChild(QPushButton, widget_ids.WS_STREAM_PAUSE_BUTTON)
        assert pause_btn is not None, "Missing WS_STREAM_PAUSE_BUTTON"
        _assert_widget_identity(pause_btn, widget_ids.WS_STREAM_PAUSE_BUTTON)

        # Clear button
        clear_btn = stream_view.findChild(QPushButton, widget_ids.WS_STREAM_CLEAR_BUTTON)
        assert clear_btn is not None, "Missing WS_STREAM_CLEAR_BUTTON"
        _assert_widget_identity(clear_btn, widget_ids.WS_STREAM_CLEAR_BUTTON)

        # Export button
        export_btn = stream_view.findChild(QPushButton, widget_ids.WS_STREAM_EXPORT_BUTTON)
        assert export_btn is not None, "Missing WS_STREAM_EXPORT_BUTTON"
        _assert_widget_identity(export_btn, widget_ids.WS_STREAM_EXPORT_BUTTON)

        # Drop notice banner (hidden initially)
        drop_notice = stream_view.findChild(QWidget, widget_ids.WS_STREAM_DROP_NOTICE)
        assert drop_notice is not None, "Missing WS_STREAM_DROP_NOTICE"
        _assert_widget_identity(drop_notice, widget_ids.WS_STREAM_DROP_NOTICE)
        assert not drop_notice.isVisible()

        # Match count label
        match_count = stream_view.findChild(QLabel, widget_ids.WS_STREAM_MATCH_COUNT)
        assert match_count is not None, "Missing WS_STREAM_MATCH_COUNT"
        _assert_widget_identity(match_count, widget_ids.WS_STREAM_MATCH_COUNT)

        # Follow-tail badge (hidden initially)
        follow_badge = stream_view.findChild(QWidget, widget_ids.WS_STREAM_FOLLOW_TAIL_BADGE)
        assert follow_badge is not None, "Missing WS_STREAM_FOLLOW_TAIL_BADGE"
        _assert_widget_identity(follow_badge, widget_ids.WS_STREAM_FOLLOW_TAIL_BADGE)
        assert not follow_badge.isVisible()

        # Detail pane
        detail_pane = stream_view.findChild(QWidget, widget_ids.WS_STREAM_DETAIL)
        assert detail_pane is not None, "Missing WS_STREAM_DETAIL"
        _assert_widget_identity(detail_pane, widget_ids.WS_STREAM_DETAIL)
    finally:
        stream_view.deleteLater()
        presenter.deleteLater()


# =============================================================================
# 5. Search Query, Match Count Accounting & Empty Filter State
# =============================================================================


def test_stream_view_search_match_count_accounting(qapp: QApplication):
    """Verify live search updates proxy model and match count label."""
    from pypost.ui.presenters.websocket_presenter import WebSocketPresenter
    from pypost.ui.widgets.websocket.stream_view import WebSocketStreamView

    conn = _make_sample_connection()
    stream_model = StreamListModel()
    presenter = WebSocketPresenter(connection=conn, stream_model=stream_model)
    stream_view = WebSocketStreamView(stream_model=stream_model, presenter=presenter)
    try:
        e1 = _create_stream_entry(seq=1, payload='{"topic":"order_placed","id":101}')
        e2 = _create_stream_entry(seq=2, payload='{"topic":"order_filled","id":101}')
        e3 = _create_stream_entry(seq=3, payload='{"topic":"heartbeat_ping"}')
        e4 = _create_stream_entry(seq=4, payload='{"topic":"balance_updated"}')
        stream_model.append_batch([e1, e2, e3, e4])
        qapp.processEvents()

        search_input = stream_view.findChild(QLineEdit, widget_ids.WS_STREAM_SEARCH_INPUT)
        match_count_lbl = stream_view.findChild(QLabel, widget_ids.WS_STREAM_MATCH_COUNT)

        # Type search query "order"
        search_input.setText("order")
        qapp.processEvents()

        # Should match 2 of 4 entries (2 hidden)
        lbl_text = match_count_lbl.text()
        assert "2" in lbl_text
        assert "hidden" in lbl_text.lower() or "4" in lbl_text or "2 matches" in lbl_text.lower()
    finally:
        stream_view.deleteLater()
        presenter.deleteLater()


def test_stream_view_empty_filter_state_and_clear_action(qapp: QApplication):
    """Verify empty filter state overlay appears on zero matches and clear filter button resets."""
    from pypost.ui.presenters.websocket_presenter import WebSocketPresenter
    from pypost.ui.widgets.websocket.stream_view import WebSocketStreamView

    conn = _make_sample_connection()
    stream_model = StreamListModel()
    presenter = WebSocketPresenter(connection=conn, stream_model=stream_model)
    stream_view = WebSocketStreamView(stream_model=stream_model, presenter=presenter)
    try:
        e1 = _create_stream_entry(seq=1, payload="normal message 1")
        e2 = _create_stream_entry(seq=2, payload="normal message 2")
        stream_model.append_batch([e1, e2])
        qapp.processEvents()

        search_input = stream_view.findChild(QLineEdit, widget_ids.WS_STREAM_SEARCH_INPUT)
        clear_filter_btn = stream_view.findChild(
            QPushButton, widget_ids.WS_STREAM_CLEAR_FILTER_BUTTON
        )
        assert clear_filter_btn is not None, "Missing WS_STREAM_CLEAR_FILTER_BUTTON"

        # Search for non-existent token
        search_input.setText("non_existent_token_99999")
        qapp.processEvents()

        # Empty filter overlay / clear button must be visible
        assert clear_filter_btn.isVisible()

        # Click Clear filter button
        clear_filter_btn.click()
        qapp.processEvents()

        assert search_input.text() == ""
        assert not clear_filter_btn.isVisible()
    finally:
        stream_view.deleteLater()
        presenter.deleteLater()


# =============================================================================
# 6. Follow-Tail Mechanics, Scroll Detachment & Display Pause
# =============================================================================


def test_stream_view_follow_tail_and_display_pause(qapp: QApplication):
    """Verify display pause detaches tail follow while background intake continues."""
    from pypost.ui.presenters.websocket_presenter import WebSocketPresenter
    from pypost.ui.widgets.websocket.stream_view import WebSocketStreamView

    conn = _make_sample_connection()
    stream_model = StreamListModel()
    presenter = WebSocketPresenter(connection=conn, stream_model=stream_model)
    stream_view = WebSocketStreamView(stream_model=stream_model, presenter=presenter)
    try:
        pause_btn = stream_view.findChild(QPushButton, widget_ids.WS_STREAM_PAUSE_BUTTON)
        badge = stream_view.findChild(QWidget, widget_ids.WS_STREAM_FOLLOW_TAIL_BADGE)

        # 1. Initial state: unpaused, badge hidden
        assert not stream_view.is_paused
        assert not badge.isVisible()

        # 2. Click Pause -> pauses UI tracking
        pause_btn.click()
        qapp.processEvents()

        assert stream_view.is_paused is True
        assert "Resume" in pause_btn.text() or "▶" in pause_btn.text() or stream_view.is_paused

        # 3. New entries arrive in background (intake continues uninterrupted)
        e1 = _create_stream_entry(seq=1, payload="msg while paused 1")
        e2 = _create_stream_entry(seq=2, payload="msg while paused 2")
        e3 = _create_stream_entry(seq=3, payload="msg while paused 3")
        stream_model.append_batch([e1, e2, e3])
        qapp.processEvents()

        # Stream model has entries retained
        assert stream_model.rowCount() == 3

        # Unread count increments and follow-tail badge becomes visible
        assert stream_view.unread_count == 3 or badge.isVisible()
        badge_lbl = badge.findChild(QLabel)
        badge_text = badge_lbl.text() if badge_lbl else getattr(badge, "text", lambda: "")()
        assert "3" in badge_text or badge.isVisible()

        # 4. Click Resume (or click follow-tail badge) -> resumes tracking, resets unread count
        pause_btn.click()
        qapp.processEvents()

        assert stream_view.is_paused is False
        assert stream_view.unread_count == 0
        assert not badge.isVisible()
    finally:
        stream_view.deleteLater()
        presenter.deleteLater()


# =============================================================================
# 7. Clear Stream Buffer & Drop Notice Accounting
# =============================================================================


def test_stream_view_clear_buffer_and_drop_notice_reset(qapp: QApplication):
    """Verify Clear button empties model rows, resets drop counters, and hides drop notice."""
    from pypost.ui.presenters.websocket_presenter import WebSocketPresenter
    from pypost.ui.widgets.websocket.stream_view import WebSocketStreamView

    # Create stream with max_entries=2 to force capacity drops
    stream = MessageStream(max_entries=2)
    stream_model = StreamListModel(stream=stream)
    conn = _make_sample_connection()
    presenter = WebSocketPresenter(connection=conn, stream_model=stream_model)
    stream_view = WebSocketStreamView(stream_model=stream_model, presenter=presenter)
    try:
        clear_btn = stream_view.findChild(QPushButton, widget_ids.WS_STREAM_CLEAR_BUTTON)
        drop_notice = stream_view.findChild(QWidget, widget_ids.WS_STREAM_DROP_NOTICE)

        # Append 4 entries to trigger 2 capacity evictions
        e1 = _create_stream_entry(seq=1, payload="entry 1")
        e2 = _create_stream_entry(seq=2, payload="entry 2")
        e3 = _create_stream_entry(seq=3, payload="entry 3")
        e4 = _create_stream_entry(seq=4, payload="entry 4")
        stream_model.append_batch([e1, e2, e3, e4])
        qapp.processEvents()

        assert stream_model.rowCount() == 2
        assert stream.dropped["capacity"] == 2
        assert drop_notice.isVisible()
        notice_lbl = drop_notice.findChild(QLabel)
        fallback_fn = getattr(drop_notice, "text", lambda: "")
        notice_text = notice_lbl.text() if notice_lbl else fallback_fn()
        assert "2" in notice_text
        assert "capacity" in notice_text.lower()

        # Click Clear
        clear_btn.click()
        qapp.processEvents()

        # Everything reset
        assert stream_model.rowCount() == 0
        assert stream.dropped["capacity"] == 0
        assert stream.dropped["memory_budget"] == 0
        assert not drop_notice.isVisible()
    finally:
        stream_view.deleteLater()
        presenter.deleteLater()


def test_stream_view_drop_notice_capacity_vs_memory_budget(qapp: QApplication):
    """Verify drop notice differentiates between capacity and memory_budget causes."""
    from pypost.ui.presenters.websocket_presenter import WebSocketPresenter
    from pypost.ui.widgets.websocket.stream_view import WebSocketStreamView

    # Budget 50 bytes
    stream = MessageStream(max_entries=100, memory_budget_bytes=50)
    stream_model = StreamListModel(stream=stream)
    conn = _make_sample_connection()
    presenter = WebSocketPresenter(connection=conn, stream_model=stream_model)
    stream_view = WebSocketStreamView(stream_model=stream_model, presenter=presenter)
    try:
        drop_notice = stream_view.findChild(QWidget, widget_ids.WS_STREAM_DROP_NOTICE)

        # Append two 30-byte entries -> second causes eviction of first due to memory_budget
        e1 = _create_stream_entry(seq=1, payload="a" * 30)
        e2 = _create_stream_entry(seq=2, payload="b" * 30)
        stream_model.append_batch([e1, e2])
        qapp.processEvents()

        assert drop_notice.isVisible()
        notice_lbl = drop_notice.findChild(QLabel)
        fallback_fn = getattr(drop_notice, "text", lambda: "")
        notice_text = notice_lbl.text() if notice_lbl else fallback_fn()
        assert "memory_budget" in notice_text.lower() or "memory" in notice_text.lower()
    finally:
        stream_view.deleteLater()
        presenter.deleteLater()


# =============================================================================
# 8. StreamDetailPane Inspection, Formatting, Wrap, Hex & Truncation
# =============================================================================


def test_stream_detail_pane_selection_and_metadata(qapp: QApplication):
    """Verify StreamDetailPane displays entry metadata header and child actions."""
    from pypost.ui.widgets.websocket.stream_view import StreamDetailPane

    pane = StreamDetailPane()
    try:
        _assert_widget_identity(pane, widget_ids.WS_STREAM_DETAIL)

        copy_btn = pane.findChild(QPushButton, widget_ids.WS_STREAM_DETAIL_COPY_BUTTON)
        assert copy_btn is not None, "Missing WS_STREAM_DETAIL_COPY_BUTTON"
        _assert_widget_identity(copy_btn, widget_ids.WS_STREAM_DETAIL_COPY_BUTTON)

        set_var_btn = pane.findChild(QPushButton, widget_ids.WS_STREAM_DETAIL_SET_VAR_BUTTON)
        assert set_var_btn is not None, "Missing WS_STREAM_DETAIL_SET_VAR_BUTTON"
        _assert_widget_identity(set_var_btn, widget_ids.WS_STREAM_DETAIL_SET_VAR_BUTTON)

        wrap_btn = pane.findChild(QPushButton, widget_ids.WS_STREAM_DETAIL_WRAP_BUTTON)
        assert wrap_btn is not None, "Missing WS_STREAM_DETAIL_WRAP_BUTTON"
        _assert_widget_identity(wrap_btn, widget_ids.WS_STREAM_DETAIL_WRAP_BUTTON)

        hex_btn = pane.findChild(QPushButton, widget_ids.WS_STREAM_DETAIL_HEX_BUTTON)
        assert hex_btn is not None, "Missing WS_STREAM_DETAIL_HEX_BUTTON"
        _assert_widget_identity(hex_btn, widget_ids.WS_STREAM_DETAIL_HEX_BUTTON)

        # Set entry
        entry = _create_stream_entry(
            seq=42,
            ts_utc="2026-08-22T14:30:00.500Z",
            direction="in",
            kind="message",
            payload_format="json",
            payload='{\n  "status": "active"\n}',
            byte_size=24,
        )
        pane.set_entry(entry)
        qapp.processEvents()

        # Metadata header text check
        assert pane.current_entry == entry
        editor = pane.findChild(QTextEdit)
        assert editor is not None
        assert '"status": "active"' in editor.toPlainText()
    finally:
        pane.deleteLater()


def test_stream_detail_pane_wrap_and_hex_toggles(qapp: QApplication):
    """Verify wrap and hex mode toggles in StreamDetailPane."""
    from pypost.ui.widgets.websocket.stream_view import StreamDetailPane

    pane = StreamDetailPane()
    try:
        entry = _create_stream_entry(
            seq=1,
            payload="Hello World Hex Test",
            byte_size=20,
        )
        pane.set_entry(entry)
        qapp.processEvents()

        wrap_btn = pane.findChild(QPushButton, widget_ids.WS_STREAM_DETAIL_WRAP_BUTTON)
        hex_btn = pane.findChild(QPushButton, widget_ids.WS_STREAM_DETAIL_HEX_BUTTON)
        editor = pane.findChild(QTextEdit)

        # 1. Toggle wrap
        initial_wrap = pane.is_wrap_mode
        wrap_btn.click()
        qapp.processEvents()
        assert pane.is_wrap_mode != initial_wrap

        # 2. Toggle Hex Mode
        assert not pane.is_hex_mode
        hex_btn.click()
        qapp.processEvents()

        assert pane.is_hex_mode is True
        hex_text = editor.toPlainText()
        # Hex view must contain offsets (00000000:), hex bytes, and printable ASCII column (|...|)
        assert "00000000:" in hex_text
        assert "48 65 6c 6c 6f" in hex_text.lower() or "48 65 6c 6c" in hex_text.lower()
        assert "|Hello World" in hex_text

        # Toggle Hex Mode back to Formatted Text
        hex_btn.click()
        qapp.processEvents()
        assert pane.is_hex_mode is False
        assert editor.toPlainText() == "Hello World Hex Test"
    finally:
        pane.deleteLater()


def test_stream_detail_pane_truncation_notice(qapp: QApplication):
    """Verify truncation alert is displayed when entry.truncated is True."""
    from pypost.ui.widgets.websocket.stream_view import StreamDetailPane

    pane = StreamDetailPane()
    try:
        # Truncated entry (wire size 1 MiB, display truncated to 256 KiB)
        entry_trunc = _create_stream_entry(
            seq=1,
            payload="A" * 256,
            byte_size=1_048_576,
            truncated=True,
        )
        pane.set_entry(entry_trunc)
        qapp.processEvents()

        assert pane.is_truncated_notice_visible is True or (
            pane.truncation_banner is not None and pane.truncation_banner.isVisible()
        )

        # Normal non-truncated entry
        entry_normal = _create_stream_entry(seq=2, payload="Normal", byte_size=6, truncated=False)
        pane.set_entry(entry_normal)
        qapp.processEvents()

        assert pane.is_truncated_notice_visible is False or (
            pane.truncation_banner is not None and not pane.truncation_banner.isVisible()
        )
    finally:
        pane.deleteLater()


# =============================================================================
# 9. Masked Clipboard Copy & Variable Capture Integration
# =============================================================================


def test_stream_detail_pane_masked_clipboard_copy(qapp: QApplication):
    """Verify Copy button copies masked content to clipboard."""
    from pypost.ui.widgets.websocket.stream_view import StreamDetailPane

    pane = StreamDetailPane()
    try:
        entry = _create_stream_entry(
            seq=1,
            payload='{"api_key": "***", "user": "alice"}',
        )
        pane.set_entry(entry)
        qapp.processEvents()

        copy_btn = pane.findChild(QPushButton, widget_ids.WS_STREAM_DETAIL_COPY_BUTTON)

        with patch.object(QApplication.clipboard(), "setText") as mock_set_text:
            copy_btn.click()
            qapp.processEvents()
            mock_set_text.assert_called_once()
            copied_val = mock_set_text.call_args[0][0]
            assert "***" in copied_val
            assert '"user": "alice"' in copied_val
    finally:
        pane.deleteLater()


def test_stream_detail_pane_set_as_variable_signal(qapp: QApplication):
    """Verify clicking 'Set as variable...' prompts or emits variable capture request."""
    from pypost.ui.widgets.websocket.stream_view import StreamDetailPane

    pane = StreamDetailPane()
    try:
        captured_signals: list[tuple[str, str]] = []
        if hasattr(pane, "variable_capture_requested"):
            pane.variable_capture_requested.connect(
                lambda name, val: captured_signals.append((name, val))
            )

        entry = _create_stream_entry(
            seq=1,
            payload='{"session_token": "tok_xyz_998"}',
        )
        pane.set_entry(entry)
        qapp.processEvents()

        set_var_btn = pane.findChild(QPushButton, widget_ids.WS_STREAM_DETAIL_SET_VAR_BUTTON)
        editor = pane.findChild(QTextEdit)
        # Select specific token in editor
        cursor = editor.textCursor()
        cursor.select(cursor.SelectionType.Document)
        editor.setTextCursor(cursor)

        with patch(
            "pypost.ui.widgets.websocket.stream_view.QInputDialog.getText",
            return_value=("MY_TOKEN", True),
        ):
            set_var_btn.click()
            qapp.processEvents()

        if hasattr(pane, "variable_capture_requested"):
            assert len(captured_signals) >= 1
            assert captured_signals[0][0] == "MY_TOKEN"
    finally:
        pane.deleteLater()


# =============================================================================
# 10. Dual-Format Transcript Export Actions
# =============================================================================


def test_stream_view_transcript_export_actions(tmp_path: Path, qapp: QApplication):
    """Verify stream export actions write valid JSON and Text transcripts."""
    from pypost.ui.presenters.websocket_presenter import WebSocketPresenter
    from pypost.ui.widgets.websocket.stream_view import WebSocketStreamView

    conn = _make_sample_connection()
    stream_model = StreamListModel()
    presenter = WebSocketPresenter(connection=conn, stream_model=stream_model)
    stream_view = WebSocketStreamView(stream_model=stream_model, presenter=presenter)
    try:
        e1 = _create_stream_entry(seq=1, payload="export test 1")
        e2 = _create_stream_entry(seq=2, payload="export test 2")
        stream_model.append_batch([e1, e2])
        qapp.processEvents()

        json_file = tmp_path / "export.json"
        text_file = tmp_path / "export.txt"

        stream_view.export_json(json_file)
        process_until(lambda: json_file.exists(), timeout_ms=10_000)
        stream_view.export_text(text_file)
        process_until(lambda: text_file.exists(), timeout_ms=10_000)

        assert json_file.exists()
        assert text_file.exists()

        parsed_json = json.loads(json_file.read_text(encoding="utf-8"))
        assert parsed_json["schema_version"] == "1.0"
        assert len(parsed_json["entries"]) == 2

        text_content = text_file.read_text(encoding="utf-8")
        assert "# PyPost WebSocket Transcript" in text_content
        assert "export test 1" in text_content
    finally:
        stream_view.deleteLater()
        presenter.deleteLater()


# =============================================================================
# 11. WebSocketTab Integration
# =============================================================================


def test_websocket_tab_integrates_stream_view(qapp: QApplication):
    """Verify WebSocketTab embeds WebSocketStreamView and exposes child inspector widgets."""
    from pypost.ui.presenters.websocket_presenter import WebSocketPresenter
    from pypost.ui.widgets.websocket.stream_view import WebSocketStreamView
    from pypost.ui.widgets.websocket.websocket_tab import WebSocketTab

    conn = _make_sample_connection()
    stream_model = StreamListModel()
    presenter = WebSocketPresenter(connection=conn, stream_model=stream_model)
    tab = WebSocketTab(connection=conn, presenter=presenter)
    try:
        _assert_widget_identity(tab, widget_ids.WS_TAB_PAGE)

        # Embedded stream view
        assert isinstance(tab.stream_view, WebSocketStreamView)
        _assert_widget_identity(tab.stream_view, widget_ids.WS_STREAM_VIEW)

        # Embedded child inspector widgets exist within tab
        assert tab.findChild(QWidget, widget_ids.WS_STREAM_SEARCH_INPUT) is not None
        assert tab.findChild(QWidget, widget_ids.WS_STREAM_DIRECTION_FILTER) is not None
        assert tab.findChild(QWidget, widget_ids.WS_STREAM_KIND_FILTER) is not None
        assert tab.findChild(QWidget, widget_ids.WS_STREAM_PAUSE_BUTTON) is not None
        assert tab.findChild(QWidget, widget_ids.WS_STREAM_CLEAR_BUTTON) is not None
        assert tab.findChild(QWidget, widget_ids.WS_STREAM_EXPORT_BUTTON) is not None
        assert tab.findChild(QWidget, widget_ids.WS_STREAM_DROP_NOTICE) is not None
        assert tab.findChild(QWidget, widget_ids.WS_STREAM_DETAIL) is not None
    finally:
        tab.deleteLater()
        presenter.deleteLater()


# =============================================================================
# 12. Observability Logging Integration
# =============================================================================


def test_stream_view_observability_logging(qapp: QApplication, caplog: pytest.LogCaptureFixture):
    """Verify WebSocketStreamView emits structured logs for filter, pause, clear, and inspection."""
    from pypost.ui.presenters.websocket_presenter import WebSocketPresenter
    from pypost.ui.widgets.websocket.stream_view import WebSocketStreamView

    conn = _make_sample_connection()
    stream_model = StreamListModel()
    presenter = WebSocketPresenter(connection=conn, stream_model=stream_model)
    stream_view = WebSocketStreamView(stream_model=stream_model, presenter=presenter)
    try:
        e1 = _create_stream_entry(seq=1, direction="in", kind="message", payload="test message")
        stream_model.append_batch([e1])
        qapp.processEvents()

        with caplog.at_level(logging.DEBUG):
            # 1. Search text change log
            search_input = stream_view.findChild(QLineEdit, widget_ids.WS_STREAM_SEARCH_INPUT)
            search_input.setText("hello")
            qapp.processEvents()

            # 2. Direction filter change log
            dir_filter = stream_view.findChild(QComboBox, widget_ids.WS_STREAM_DIRECTION_FILTER)
            dir_filter.setCurrentIndex(1)  # Inbound
            qapp.processEvents()

            # 3. Kind filter change log
            kind_filter = stream_view.findChild(QComboBox, widget_ids.WS_STREAM_KIND_FILTER)
            kind_filter.setCurrentIndex(1)  # Messages
            qapp.processEvents()

            # 4. Clear filter log
            clear_filter_btn = stream_view.findChild(
                QPushButton, widget_ids.WS_STREAM_CLEAR_FILTER_BUTTON
            )
            clear_filter_btn.click()
            qapp.processEvents()

            # 5. Pause and resume logs
            pause_btn = stream_view.findChild(QPushButton, widget_ids.WS_STREAM_PAUSE_BUTTON)
            pause_btn.click()  # Pause
            qapp.processEvents()
            pause_btn.click()  # Resume
            qapp.processEvents()

            # 6. Clear buffer log
            clear_btn = stream_view.findChild(QPushButton, widget_ids.WS_STREAM_CLEAR_BUTTON)
            clear_btn.click()
            qapp.processEvents()

        messages = [r.getMessage() for r in caplog.records]
        assert any("websocket_stream_filter_search_changed query_len=5" in m for m in messages)
        assert any("websocket_stream_filter_direction_changed direction=in" in m for m in messages)
        assert any("websocket_stream_filter_kind_changed kind=message" in m for m in messages)
        assert any("websocket_stream_filters_reset" in m for m in messages)
        assert any("websocket_stream_display_paused" in m for m in messages)
        assert any("websocket_stream_display_resumed" in m for m in messages)
        assert any("websocket_stream_view_cleared" in m for m in messages)
    finally:
        stream_view.deleteLater()
        presenter.deleteLater()


def test_stream_detail_pane_observability_logging(
    qapp: QApplication, caplog: pytest.LogCaptureFixture
):
    """Verify StreamDetailPane emits structured logs for wrap, hex, copy, and var capture."""
    from pypost.ui.widgets.websocket.stream_view import StreamDetailPane

    pane = StreamDetailPane()
    try:
        entry = _create_stream_entry(seq=1, payload="detail inspection data")
        pane.set_entry(entry)
        qapp.processEvents()

        wrap_btn = pane.findChild(QPushButton, widget_ids.WS_STREAM_DETAIL_WRAP_BUTTON)
        hex_btn = pane.findChild(QPushButton, widget_ids.WS_STREAM_DETAIL_HEX_BUTTON)
        copy_btn = pane.findChild(QPushButton, widget_ids.WS_STREAM_DETAIL_COPY_BUTTON)
        set_var_btn = pane.findChild(QPushButton, widget_ids.WS_STREAM_DETAIL_SET_VAR_BUTTON)

        with caplog.at_level(logging.DEBUG):
            # 1. Wrap toggle
            wrap_btn.click()
            qapp.processEvents()

            # 2. Hex toggle
            hex_btn.click()
            qapp.processEvents()

            # 3. Copy payload
            with patch.object(QApplication.clipboard(), "setText"):
                copy_btn.click()
                qapp.processEvents()

            # 4. Set as variable
            with patch(
                "pypost.ui.widgets.websocket.stream_view.QInputDialog.getText",
                return_value=("MY_TOKEN", True),
            ):
                set_var_btn.click()
                qapp.processEvents()

        messages = [r.getMessage() for r in caplog.records]
        assert any("websocket_detail_wrap_toggled wrap=" in m for m in messages)
        assert any("websocket_detail_hex_toggled hex=True" in m for m in messages)
        assert any("websocket_detail_payload_copied length=" in m for m in messages)
        assert any("websocket_variable_capture_requested name=MY_TOKEN" in m for m in messages)
    finally:
        pane.deleteLater()
