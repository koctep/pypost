"""Failing repro tests for WS-7 WebSocket Environments, Templating, and Secret Masking.

Task: PYPOST-1135.
Asserts the contract and behavior specified in:
- `ai-tasks/PYPOST-1135/10-requirements.md`
- `ai-tasks/PYPOST-1135/20-architecture.md`
- `ai-tasks/PYPOST-1124/20-architecture.md` (Sections A-13.7, A-8.2, A-8.4)

Covers:
1. Connect-time resolution: URL, query params, headers, subprotocols resolve once upon connect
   and are frozen for the session duration; mid-session environment changes do not mutate the
   active connection handshake.
2. Per-send payload resolution: composer, preset, sequence step templates (e.g. {{ token }})
   resolve dynamically at send time; updating variables mid-session affects next send immediately.
3. Inbound literal safety: server-received payloads containing {{ secret }} or template syntax
   are never evaluated by the template engine and remain literal data.
4. Two-tier secret masking:
   - Tier 1: exact replacement on live stream (build_stream_entry replaces hidden values with ***).
   - Tier 2: heuristic egress sanitization (sanitize_text) for clipboard copy, JSON/text exports,
     and logs.
5. UI hover tooltips: hovering {{ VAR }} shows resolved value or ******** when hidden.
6. Metric accounting: hidden_value_masks_applied_total{surface="websocket"} incremented when
   masking applied.
7. Ring ownership & seam invariants: presenter coordinates env/masking, StreamListModel is sole
   ring writer, WebSocketSessionController remains environment-free.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Optional
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import (
    QApplication,
    QPushButton,
)

from pypost.core.metrics_registry import MetricsRegistry
from pypost.core.websocket_session_policy import SessionState
from pypost.core.websocket_stream import (
    MessageStream,
    StreamEntry,
    build_stream_entry,
)
from pypost.core.websocket_stream_export import (
    export_stream_to_json_file,
    export_stream_to_text_file,
    format_json_transcript,
    format_text_transcript,
)
from pypost.core.websocket_transport_protocol import (
    FrameDirection,
    FrameType,
    HandshakeTarget,
    RawFrame,
)
from pypost.models.websocket import (
    WebSocketConnection,
    WebSocketMessagePreset,
    WebSocketSequence,
    WebSocketSequenceStep,
    WsMessageFormat,
)
from pypost.ui import widget_ids
from pypost.ui.presenters.websocket_presenter import WebSocketPresenter
from pypost.ui.widgets.variable_aware_widgets import (
    VariableAwareLineEdit,
    VariableAwareTableWidget,
)
from pypost.ui.widgets.websocket.composer import WebSocketComposer
from pypost.ui.widgets.websocket.connection_editor import WebSocketConnectionEditor
from pypost.ui.widgets.websocket.stream_view import StreamDetailPane
from pypost.ui.widgets.websocket.websocket_tab import WebSocketTab

pytestmark = pytest.mark.timeout(30)


# =============================================================================
# Helper Fixtures & Builders
# =============================================================================


def _make_connection_with_templates() -> WebSocketConnection:
    """Create a sample WebSocketConnection parameterized with {{ ... }} templates."""
    return WebSocketConnection(
        id="ws_env_test",
        name="Templated WebSocket",
        url="wss://{{ WS_HOST }}/v1/feed",
        headers={
            "Authorization": "Bearer {{ WS_TOKEN }}",
            "X-Client-Id": "{{ CLIENT_ID }}",
        },
        params={
            "channel": "{{ CHANNEL }}",
            "apiKey": "{{ API_KEY }}",
        },
        subprotocols=["proto.{{ PROTO_VER }}", "json.v2"],
        presets=[
            WebSocketMessagePreset(
                id="preset_auth",
                name="Auth Request",
                format=WsMessageFormat.JSON,
                payload='{"action": "authenticate", "token": "{{ WS_TOKEN }}"}',
            ),
        ],
        sequences=[
            WebSocketSequence(
                id="seq_login_sub",
                name="Login & Sub",
                steps=[
                    WebSocketSequenceStep(preset_id="preset_auth", delay_ms=0),
                    WebSocketSequenceStep(
                        inline_payload='{"action": "subscribe", "ch": "{{ CHANNEL }}"}',
                        format=WsMessageFormat.TEXT,
                        delay_ms=50,
                    ),
                ],
            )
        ],
    )


def _make_sample_raw_frame(
    payload: str | bytes,
    direction: FrameDirection = FrameDirection.IN,
    frame_type: FrameType = FrameType.TEXT,
) -> RawFrame:
    return RawFrame(
        direction=direction,
        payload_format=frame_type,
        payload=payload,
        byte_size=len(payload.encode("utf-8") if isinstance(payload, str) else payload),
        timestamp=datetime.now(timezone.utc),
    )


# =============================================================================
# 1. Connect-Time Handshake Template Resolution
# =============================================================================


def test_connect_time_resolution_resolves_url_headers_params_subprotocols(qapp: QApplication):
    """Verify handle_connect resolves URL, headers, params, and subprotocols via TemplateService."""
    conn = _make_connection_with_templates()
    env_vars = {
        "WS_HOST": "stream.staging.example.com",
        "WS_TOKEN": "secret_token_abc123",
        "CLIENT_ID": "client_99",
        "CHANNEL": "orders",
        "API_KEY": "key_xyz",
        "PROTO_VER": "v1",
    }
    hidden_keys = {"WS_TOKEN", "API_KEY"}

    presenter = WebSocketPresenter(
        connection=conn,
        env_vars=env_vars,
        hidden_keys=hidden_keys,
    )
    tab = WebSocketTab(conn, presenter)
    presenter.set_tab(tab)
    qapp.processEvents()

    try:
        with patch.object(presenter.session_controller, "open") as mock_open:
            presenter.handle_connect()
            qapp.processEvents()

            mock_open.assert_called_once()
            target: HandshakeTarget = mock_open.call_args[0][0]

            # URL and merged query params should be resolved
            assert "stream.staging.example.com" in target.url
            assert "orders" in target.url
            assert "key_xyz" in target.url
            assert "{{" not in target.url

            # Headers should be resolved
            assert target.headers.get("Authorization") == "Bearer secret_token_abc123"
            assert target.headers.get("X-Client-Id") == "client_99"

            # Subprotocols should be resolved
            assert "proto.v1" in target.subprotocols
            assert "json.v2" in target.subprotocols
    finally:
        presenter.teardown()
        tab.deleteLater()


def test_connect_time_parameters_frozen_mid_session(qapp: QApplication):
    """Verify modifying environment variables mid-session does not alter active handshake."""
    conn = _make_connection_with_templates()
    env_vars = {
        "WS_HOST": "staging.example.com",
        "WS_TOKEN": "token_stg",
        "CLIENT_ID": "client_1",
        "CHANNEL": "feed",
        "API_KEY": "key_1",
        "PROTO_VER": "v1",
    }
    hidden_keys = {"WS_TOKEN"}

    presenter = WebSocketPresenter(
        connection=conn,
        env_vars=env_vars,
        hidden_keys=hidden_keys,
    )
    tab = WebSocketTab(conn, presenter)
    presenter.set_tab(tab)
    qapp.processEvents()

    try:
        opened_target: Optional[HandshakeTarget] = None

        def fake_open(target: HandshakeTarget, **kwargs):
            nonlocal opened_target
            opened_target = target
            presenter._on_state_changed(SessionState.OPEN.value)

        with patch.object(presenter.session_controller, "open", side_effect=fake_open):
            presenter.handle_connect()
            qapp.processEvents()

        assert opened_target is not None
        assert "staging.example.com" in opened_target.url
        assert opened_target.headers["Authorization"] == "Bearer token_stg"

        # Update environment variables mid-session
        presenter.set_variables({
            "WS_HOST": "production.example.com",
            "WS_TOKEN": "token_prod",
            "CLIENT_ID": "client_2",
            "CHANNEL": "live",
            "API_KEY": "key_prod",
            "PROTO_VER": "v2",
        })
        qapp.processEvents()

        # Active handshake target remains frozen
        assert "staging.example.com" in opened_target.url
        assert opened_target.headers["Authorization"] == "Bearer token_stg"
    finally:
        presenter.teardown()
        tab.deleteLater()


def test_reconnect_applies_updated_environment_variables(qapp: QApplication):
    """Verify reconnecting after environment change resolves the new variables."""
    conn = _make_connection_with_templates()
    env_vars = {
        "WS_HOST": "staging.example.com",
        "WS_TOKEN": "token_stg",
        "CLIENT_ID": "client_1",
        "CHANNEL": "feed",
        "API_KEY": "key_1",
        "PROTO_VER": "v1",
    }

    presenter = WebSocketPresenter(connection=conn, env_vars=env_vars)
    tab = WebSocketTab(conn, presenter)
    presenter.set_tab(tab)
    qapp.processEvents()

    try:
        opened_targets: list[HandshakeTarget] = []

        def fake_open(target: HandshakeTarget, **kwargs):
            opened_targets.append(target)
            presenter._on_state_changed(SessionState.OPEN.value)

        with patch.object(presenter.session_controller, "open", side_effect=fake_open):
            presenter.handle_connect()
            qapp.processEvents()

            assert len(opened_targets) == 1
            assert "staging.example.com" in opened_targets[0].url

            # Disconnect
            presenter.handle_disconnect()
            presenter._on_state_changed(SessionState.CLOSED.value)
            qapp.processEvents()

            # Switch environment variables
            presenter.set_variables({
                "WS_HOST": "production.example.com",
                "WS_TOKEN": "token_prod",
                "CLIENT_ID": "client_prod",
                "CHANNEL": "live",
                "API_KEY": "key_prod",
                "PROTO_VER": "v2",
            })
            qapp.processEvents()

            # Reconnect
            presenter.handle_connect()
            qapp.processEvents()

            assert len(opened_targets) == 2
            assert "production.example.com" in opened_targets[1].url
            assert opened_targets[1].headers["Authorization"] == "Bearer token_prod"
            assert "proto.v2" in opened_targets[1].subprotocols
    finally:
        presenter.teardown()
        tab.deleteLater()


# =============================================================================
# 2. Per-Send Outgoing Payload Dynamic Resolution
# =============================================================================


def test_composer_send_resolves_payload_dynamically_at_send_time(qapp: QApplication):
    """Verify composer evaluates {{ VAR }} dynamically at send time over the wire."""
    conn = _make_connection_with_templates()
    env_vars = {"ORDER_ID": "ORD-1001", "WS_TOKEN": "initial_token"}
    hidden_keys = {"WS_TOKEN"}

    presenter = WebSocketPresenter(
        connection=conn,
        env_vars=env_vars,
        hidden_keys=hidden_keys,
    )
    tab = WebSocketTab(conn, presenter)
    presenter.set_tab(tab)
    presenter._on_state_changed(SessionState.OPEN.value)
    qapp.processEvents()

    try:
        sent_texts: list[str] = []
        with patch.object(presenter.session_controller, "send_text", side_effect=sent_texts.append):
            tab.composer.set_format(WsMessageFormat.TEXT)
            tab.composer.set_payload('{"order": "{{ ORDER_ID }}", "auth": "{{ WS_TOKEN }}"}')
            qapp.processEvents()

            tab.composer.send_current_payload()
            qapp.processEvents()

            assert len(sent_texts) == 1
            # The payload sent over the wire MUST be resolved
            assert '{"order": "ORD-1001", "auth": "initial_token"}' == sent_texts[0]

            # Update environment variable mid-session (e.g. captured order ID)
            presenter.set_variables({"ORDER_ID": "ORD-9999", "WS_TOKEN": "updated_token"})
            qapp.processEvents()

            tab.composer.set_payload('{"order": "{{ ORDER_ID }}", "auth": "{{ WS_TOKEN }}"}')
            tab.composer.send_current_payload()
            qapp.processEvents()

            assert len(sent_texts) == 2
            assert '{"order": "ORD-9999", "auth": "updated_token"}' == sent_texts[1]
    finally:
        presenter.teardown()
        tab.deleteLater()


def test_sequence_runner_resolves_step_templates_dynamically(qapp: QApplication):
    """Verify sequence runner dynamically resolves templates in steps."""
    conn = _make_connection_with_templates()
    env_vars = {
        "WS_TOKEN": "seq_secret_tok",
        "CHANNEL": "forex",
    }
    hidden_keys = {"WS_TOKEN"}

    presenter = WebSocketPresenter(
        connection=conn,
        env_vars=env_vars,
        hidden_keys=hidden_keys,
    )
    tab = WebSocketTab(conn, presenter)
    presenter.set_tab(tab)
    presenter._on_state_changed(SessionState.OPEN.value)
    qapp.processEvents()

    try:
        sent_payloads: list[str] = []
        with patch.object(
            presenter.session_controller, "send_text", side_effect=sent_payloads.append
        ):
            ok = presenter.run_sequence("seq_login_sub")
            assert ok is True
            import time
            deadline = time.time() + 2.0
            while len(sent_payloads) < 2 and time.time() < deadline:
                qapp.processEvents()
                time.sleep(0.01)

            # Sequence step 1 is preset_auth, step 2 is inline subscribe
            # Both must resolve templates
            assert any("seq_secret_tok" in p for p in sent_payloads)
            assert any("forex" in p for p in sent_payloads)
    finally:
        presenter.teardown()
        tab.deleteLater()


# =============================================================================
# 3. Inbound Frame Literal Safety Invariant
# =============================================================================


def test_inbound_frames_are_never_rendered_by_template_service(qapp: QApplication):
    """Verify received server frames containing template syntax remain literal data."""
    conn = _make_connection_with_templates()
    env_vars = {
        "SECRET_VAL": "real_secret_do_not_leak",
        "CLIENT_ID": "12345",
    }
    hidden_keys = {"SECRET_VAL"}

    presenter = WebSocketPresenter(
        connection=conn,
        env_vars=env_vars,
        hidden_keys=hidden_keys,
    )
    tab = WebSocketTab(conn, presenter)
    presenter.set_tab(tab)
    qapp.processEvents()

    try:
        # Simulate incoming server message that contains template tags
        inbound_payload = '{"server_echo": "{{ SECRET_VAL }}", "calc": "{{ 7 * 7 }}"}'
        raw_frame = _make_sample_raw_frame(inbound_payload, FrameDirection.IN)

        presenter._on_frame_received(raw_frame)
        presenter._on_flush_timer()
        qapp.processEvents()

        # Check stream model entry
        assert presenter.stream_model.rowCount() == 1
        entry = presenter.stream_model.get_entry(0)
        assert entry is not None

        # Inbound frame MUST NOT have evaluated {{ SECRET_VAL }} or {{ 7 * 7 }}
        assert "{{ SECRET_VAL }}" in entry.payload
        assert "{{ 7 * 7 }}" in entry.payload
        assert "real_secret_do_not_leak" not in entry.payload
        assert "49" not in entry.payload
    finally:
        presenter.teardown()
        tab.deleteLater()


# =============================================================================
# 4. Two-Tier Secret Masking Framework
# =============================================================================


def test_tier1_masking_exact_replacement_on_stream_ingestion(qapp: QApplication):
    """Verify Tier 1 exact hidden-variable replacement with *** in StreamEntry."""
    env_vars = {"API_KEY": "super_secret_key_123", "VISIBLE_USER": "alice"}
    hidden_keys = {"API_KEY"}

    # 1. Outbound frame containing hidden secret
    out_frame = _make_sample_raw_frame(
        '{"api_key": "super_secret_key_123", "user": "alice"}',
        direction=FrameDirection.OUT,
    )
    entry_out = build_stream_entry(
        out_frame,
        seq=1,
        env_vars=env_vars,
        hidden_keys=hidden_keys,
    )
    assert '{"api_key": "***", "user": "alice"}' == entry_out.payload
    assert "super_secret_key_123" not in entry_out.payload

    # 2. Inbound frame echoed by server containing hidden secret
    in_frame = _make_sample_raw_frame(
        '{"echo_key": "super_secret_key_123", "status": "ok"}',
        direction=FrameDirection.IN,
    )
    entry_in = build_stream_entry(
        in_frame,
        seq=2,
        env_vars=env_vars,
        hidden_keys=hidden_keys,
    )
    assert '{"echo_key": "***", "status": "ok"}' == entry_in.payload
    assert "super_secret_key_123" not in entry_in.payload

    # 3. Lifecycle event containing hidden secret
    entry_lifecycle = build_stream_entry(
        None,
        seq=3,
        kind="lifecycle",
        direction="none",
        payload="Connected to wss://example.com?token=super_secret_key_123",
        detail="token=super_secret_key_123",
        env_vars=env_vars,
        hidden_keys=hidden_keys,
    )
    assert "super_secret_key_123" not in entry_lifecycle.payload
    assert "***" in entry_lifecycle.payload
    assert "super_secret_key_123" not in entry_lifecycle.detail


def test_tier2_detail_pane_clipboard_copy_applies_sanitize_text(qapp: QApplication):
    """Verify Detail Pane clipboard copy applies Tier 2 heuristic sanitization."""
    pane = StreamDetailPane()
    try:
        # Set environment variables and hidden keys on pane or presenter
        env_vars = {"MY_SECRET": "cust_secret_999"}
        hidden_keys = {"MY_SECRET"}

        # Text with both hidden env var and heuristic pattern (Bearer token)
        entry = StreamEntry(
            seq=1,
            ts_utc="2026-08-23T12:00:00.000Z",
            kind="message",
            direction="in",
            payload_format="json",
            payload='{"token": "cust_secret_999", "header": "Bearer eyJhbGciOiJIUzI1NiJ9.abc.xyz"}',
            byte_size=100,
        )
        pane.set_entry(entry)
        if hasattr(pane, "set_variables"):
            pane.set_variables(env_vars)
        if hasattr(pane, "set_hidden_keys"):
            pane.set_hidden_keys(hidden_keys)
        qapp.processEvents()

        copy_btn = pane.findChild(QPushButton, widget_ids.WS_STREAM_DETAIL_COPY_BUTTON)
        assert copy_btn is not None

        with patch.object(QApplication.clipboard(), "setText") as mock_set_text:
            copy_btn.click()
            qapp.processEvents()

            mock_set_text.assert_called_once()
            copied_text = mock_set_text.call_args[0][0]

            assert "cust_secret_999" not in copied_text
            assert "eyJhbGciOiJIUzI1NiJ9" not in copied_text
            assert "***" in copied_text
    finally:
        pane.deleteLater()


def test_tier2_json_and_text_transcript_export_applies_sanitization(tmp_path: Path):
    """Verify dual-format transcript export applies Tier 2 heuristic sanitization."""
    stream = MessageStream()
    stream.append(
        StreamEntry(
            seq=1,
            ts_utc="2026-08-23T12:00:00.000Z",
            kind="message",
            direction="out",
            payload_format="json",
            payload='{"auth": "Bearer secret_jwt_token_12345", "env_secret": "my_hidden_pass"}',
            byte_size=80,
        )
    )
    stream.append(
        StreamEntry(
            seq=2,
            ts_utc="2026-08-23T12:00:01.000Z",
            kind="lifecycle",
            direction="none",
            payload_format="text",
            payload="[CONNECTED] ws://api.io?api_key=my_hidden_pass",
            byte_size=40,
            detail="ws://api.io?api_key=my_hidden_pass",
        )
    )

    env_vars = {"PASS_KEY": "my_hidden_pass"}
    hidden_keys = {"PASS_KEY"}

    # JSON export format test
    json_data = format_json_transcript(stream, env_vars=env_vars, hidden_keys=hidden_keys)
    json_str = json.dumps(json_data)
    assert "secret_jwt_token_12345" not in json_str
    assert "my_hidden_pass" not in json_str
    assert "***" in json_str

    # JSON file export test
    json_path = tmp_path / "transcript.json"
    export_stream_to_json_file(json_path, stream, env_vars=env_vars, hidden_keys=hidden_keys)
    disk_json_content = json_path.read_text(encoding="utf-8")
    assert "secret_jwt_token_12345" not in disk_json_content
    assert "my_hidden_pass" not in disk_json_content

    # Text export format test
    text_data = format_text_transcript(stream, env_vars=env_vars, hidden_keys=hidden_keys)
    assert "secret_jwt_token_12345" not in text_data
    assert "my_hidden_pass" not in text_data

    # Text file export test
    text_path = tmp_path / "transcript.txt"
    export_stream_to_text_file(text_path, stream, env_vars=env_vars, hidden_keys=hidden_keys)
    disk_text_content = text_path.read_text(encoding="utf-8")
    assert "secret_jwt_token_12345" not in disk_text_content
    assert "my_hidden_pass" not in disk_text_content


def test_zero_secret_leakage_in_presenter_and_export_logging(
    qapp: QApplication, caplog: pytest.LogCaptureFixture
):
    """Verify sensitive payloads, secret headers, and query secrets never leak to logs."""
    conn = _make_connection_with_templates()
    env_vars = {
        "WS_HOST": "echo.example.com",
        "WS_TOKEN": "super_secret_auth_token_999",
        "CLIENT_ID": "client_1",
        "CHANNEL": "trades",
        "API_KEY": "api_secret_key_888",
        "PROTO_VER": "v1",
    }
    hidden_keys = {"WS_TOKEN", "API_KEY"}

    presenter = WebSocketPresenter(
        connection=conn,
        env_vars=env_vars,
        hidden_keys=hidden_keys,
    )
    tab = WebSocketTab(conn, presenter)
    presenter.set_tab(tab)
    qapp.processEvents()

    try:
        with caplog.at_level(logging.DEBUG):
            presenter.handle_connect()
            qapp.processEvents()

        log_text = caplog.text
        # Assert no plaintext secrets in log messages
        assert "super_secret_auth_token_999" not in log_text
        assert "api_secret_key_888" not in log_text
    finally:
        presenter.teardown()
        tab.deleteLater()


# =============================================================================
# 5. Interactive Variable Hover Tooltips Across WebSocket UI
# =============================================================================


def test_variable_hover_tooltips_on_connection_editor(qapp: QApplication):
    """Verify VariableAwareLineEdit/TableWidget show resolved or masked tooltips."""
    editor = WebSocketConnectionEditor()
    try:
        env_vars = {
            "WS_HOST": "stream.staging.org",
            "SECRET_TOKEN": "sec_val_456",
        }
        hidden_keys = {"SECRET_TOKEN"}

        editor.set_variables(env_vars)
        editor.set_hidden_keys(hidden_keys)
        editor.set_data(
            url="wss://{{ WS_HOST }}/v1/stream",
            headers={"Authorization": "Bearer {{ SECRET_TOKEN }}"},
            params={"host": "{{ WS_HOST }}"},
            subprotocols=["proto.{{ WS_HOST }}"],
        )
        qapp.processEvents()

        # 1. URL Input hover
        url_input = editor.findChild(VariableAwareLineEdit, widget_ids.WS_URL_INPUT)
        assert url_input is not None
        assert url_input._variables == env_vars
        assert url_input._hidden_keys == hidden_keys

        # 2. Subprotocols Input hover
        sub_input = editor.findChild(VariableAwareLineEdit, widget_ids.WS_SUBPROTOCOLS_INPUT)
        assert sub_input is not None
        assert sub_input._variables == env_vars

        # 3. Headers table hover
        headers_table = editor.headers_table
        assert isinstance(headers_table, VariableAwareTableWidget)
        assert headers_table._variables == env_vars
        assert headers_table._hidden_keys == hidden_keys

        # Cell resolving SECRET_TOKEN must resolve to masked ********
        resolved_secret = headers_table._resolve_cell_hover(headers_table.item(0, 1))
        assert resolved_secret is not None
        assert "sec_val_456" not in resolved_secret
        assert "********" in resolved_secret

        # Cell resolving WS_HOST must resolve to stream.staging.org
        params_table = editor.params_table
        resolved_host = params_table._resolve_cell_hover(params_table.item(0, 1))
        assert resolved_host is not None
        assert "stream.staging.org" in resolved_host
    finally:
        editor.deleteLater()


def test_variable_hover_tooltips_on_composer(qapp: QApplication):
    """Verify composer payload edit supports variable hover inspection."""
    composer = WebSocketComposer()
    try:
        env_vars = {"ORDER_NUM": "ORD-777", "SECRET_KEY": "shh_top_secret"}
        hidden_keys = {"SECRET_KEY"}

        if hasattr(composer, "set_variables"):
            composer.set_variables(env_vars)
        if hasattr(composer, "set_hidden_keys"):
            composer.set_hidden_keys(hidden_keys)

        composer.set_payload('{"order": "{{ ORDER_NUM }}", "key": "{{ SECRET_KEY }}"}')
        qapp.processEvents()

        payload_edit = composer.payload_edit
        # Payload edit must have variables set
        assert getattr(payload_edit, "_variables", None) == env_vars
        assert getattr(payload_edit, "_hidden_keys", None) == hidden_keys
    finally:
        composer.deleteLater()


def test_presenter_propagates_environment_changes_to_child_widgets(qapp: QApplication):
    """Verify presenter.set_variables and set_hidden_keys propagate snapshots to tab widgets."""
    conn = _make_connection_with_templates()
    presenter = WebSocketPresenter(connection=conn)
    tab = WebSocketTab(conn, presenter)
    presenter.set_tab(tab)
    qapp.processEvents()

    try:
        new_vars = {"BASE": "wss://test.io", "PASS": "12345"}
        new_hidden = {"PASS"}

        presenter.set_variables(new_vars)
        presenter.set_hidden_keys(new_hidden)
        qapp.processEvents()

        # Check connection editor
        assert tab.connection_editor.url_input._variables == new_vars
        assert tab.connection_editor.headers_table._hidden_keys == new_hidden

        # Check composer
        if hasattr(tab.composer, "payload_edit"):
            assert getattr(tab.composer.payload_edit, "_variables", None) == new_vars
            assert getattr(tab.composer.payload_edit, "_hidden_keys", None) == new_hidden
    finally:
        presenter.teardown()
        tab.deleteLater()


# =============================================================================
# 6. Metric Accounting
# =============================================================================


def test_hidden_value_masks_applied_metric_incremented_on_masking():
    """Verify hidden_value_masks_applied_total{surface="websocket"} counter increments."""
    metrics = MetricsRegistry()
    env_vars = {"SECRET_KEY": "secret_abc_123"}
    hidden_keys = {"SECRET_KEY"}

    frame = _make_sample_raw_frame(
        '{"token": "secret_abc_123"}',
        direction=FrameDirection.OUT,
    )

    # Initial metric counter
    before = metrics.hidden_value_masks_applied.labels(surface="websocket")._value.get()

    def on_mask():
        metrics.track_hidden_value_mask_applied(surface="websocket")

    entry = build_stream_entry(
        frame,
        seq=1,
        env_vars=env_vars,
        hidden_keys=hidden_keys,
        on_mask_applied=on_mask,
    )

    assert entry.payload == '{"token": "***"}'
    after = metrics.hidden_value_masks_applied.labels(surface="websocket")._value.get()
    assert after == before + 1


def test_presenter_increments_metric_when_masking_frames(qapp: QApplication):
    """Verify presenter increments metric registry counter when masking frames."""
    conn = _make_connection_with_templates()
    metrics = MetricsRegistry()
    env_vars = {"SECRET": "super_token_99"}
    hidden_keys = {"SECRET"}

    presenter = WebSocketPresenter(
        connection=conn,
        env_vars=env_vars,
        hidden_keys=hidden_keys,
        metrics=metrics,
    )
    tab = WebSocketTab(conn, presenter)
    presenter.set_tab(tab)
    qapp.processEvents()

    try:
        before = metrics.hidden_value_masks_applied.labels(surface="websocket")._value.get()

        # Outbound frame with secret
        out_frame = _make_sample_raw_frame('{"msg": "super_token_99"}', FrameDirection.OUT)
        presenter._on_frame_sent(out_frame)
        presenter._on_flush_timer()
        qapp.processEvents()

        after_out = metrics.hidden_value_masks_applied.labels(surface="websocket")._value.get()
        assert after_out > before

        # Inbound frame with secret
        in_frame = _make_sample_raw_frame('{"resp": "super_token_99"}', FrameDirection.IN)
        presenter._on_frame_received(in_frame)
        presenter._on_flush_timer()
        qapp.processEvents()

        after_in = metrics.hidden_value_masks_applied.labels(surface="websocket")._value.get()
        assert after_in > after_out
    finally:
        presenter.teardown()
        tab.deleteLater()


# =============================================================================
# 7. Ring Ownership & Seam Invariants
# =============================================================================


def test_architectural_seam_controller_is_environment_free():
    """Verify WebSocketSessionController does not reference or depend on environments/secrets."""
    from pypost.core.qt.websocket_session import WebSocketSessionController

    controller = WebSocketSessionController()
    try:
        # Controller must not have environment variable attributes
        assert not hasattr(controller, "_env_vars")
        assert not hasattr(controller, "_hidden_keys")
        assert not hasattr(controller, "set_variables")
        assert not hasattr(controller, "set_hidden_keys")
    finally:
        controller.deleteLater()


def test_stream_list_model_is_sole_ring_writer(qapp: QApplication):
    """Verify StreamListModel.append_batch is the sole writer to MessageStream."""
    conn = _make_connection_with_templates()
    presenter = WebSocketPresenter(connection=conn)
    tab = WebSocketTab(conn, presenter)
    presenter.set_tab(tab)
    qapp.processEvents()

    try:
        stream = presenter.stream_model.stream
        assert len(stream) == 0

        frame = _make_sample_raw_frame("test payload")
        presenter._on_frame_received(frame)
        presenter._on_flush_timer()
        qapp.processEvents()

        assert len(stream) == 1
    finally:
        presenter.teardown()
        tab.deleteLater()
