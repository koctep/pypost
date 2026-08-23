"""Failing repro tests for WS-6 WebSocket Composer, saved presets, and sequence runner.

Asserts the contract and behavior specified in:
- `ai-tasks/PYPOST-1134/10-requirements.md`
- `ai-tasks/PYPOST-1134/20-architecture.md`
- `ai-tasks/PYPOST-1124/20-architecture.md` (Sections A-5.4, A-5.5, A-13.6)

Covers:
1. Multi-format payload composition and pre-send validation (Text, JSON, Hex, Base64).
2. Preset CRUD, persistence, duplication, deletion, "Load into composer", and "Send now".
3. Sequence plan compilation (`compile_sequence_plan`), ordered step pacing with `delay_ms`,
   and missing preset safety blocker (`<missing preset>`).
4. Async Qt sequence runner (`WebSocketSequenceRunner`) running steps against session controller,
   mid-run stop leaving session open, runtime error stop on step failure, and variable resolution.
5. Messages sub-tab (`pypost_ws_messages_tab` / `WS_MESSAGES_TAB`) master/detail UI, steps table,
   and informative empty states for presets and sequences.
6. Disconnected session send/run refusal guard.
7. Automation widget identities (`WS_COMPOSER_*`, `WS_PRESET_*`, `WS_SEQUENCE_*`,
   `WS_MESSAGES_TAB`).
"""

from __future__ import annotations

import logging
import time
from typing import Optional
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QObject
from PySide6.QtWidgets import (
    QComboBox,
    QPushButton,
    QTabWidget,
    QWidget,
)

from pypost.core.websocket_session_policy import (
    SessionState,
)
from pypost.models.settings import AppSettings
from pypost.models.websocket import (
    WebSocketConnection,
    WebSocketMessagePreset,
    WebSocketSequence,
    WebSocketSequenceStep,
    WsMessageFormat,
)

from pypost.core.websocket_sequence import (
    SequenceExecutionPlan,
    SequenceRunOutcome,
    StepExecutionResult,
    compile_sequence_plan,
)
from pypost.core.qt.websocket_sequence_runner import (
    WebSocketSequenceRunner,
)
from pypost.ui import widget_ids
from pypost.ui.widgets.websocket.composer import WebSocketComposer
from pypost.ui.widgets.websocket.presets_panel import WebSocketPresetsPanel
from pypost.ui.widgets.websocket.websocket_tab import WebSocketTab
from pypost.ui.presenters.websocket_presenter import WebSocketPresenter

pytestmark = pytest.mark.timeout(30)


# =============================================================================
# Helper Fixtures & Builders
# =============================================================================


def _make_sample_connection_with_presets() -> WebSocketConnection:
    """Create a sample WebSocketConnection with populated presets and sequences."""
    p1 = WebSocketMessagePreset(
        id="preset_auth",
        name="Auth Login",
        format=WsMessageFormat.JSON,
        payload='{"action": "auth", "token": "{{AUTH_TOKEN}}"}',
    )
    p2 = WebSocketMessagePreset(
        id="preset_ping",
        name="Heartbeat Ping",
        format=WsMessageFormat.TEXT,
        payload="ping",
    )
    p3 = WebSocketMessagePreset(
        id="preset_binary",
        name="Binary Query",
        format=WsMessageFormat.HEX,
        payload="48656c6c6f",
    )

    seq_step1 = WebSocketSequenceStep(preset_id="preset_auth", delay_ms=0)
    seq_step2 = WebSocketSequenceStep(preset_id="preset_ping", delay_ms=100)
    seq_step3 = WebSocketSequenceStep(
        inline_payload="sub:trades",
        format=WsMessageFormat.TEXT,
        delay_ms=250,
    )

    seq1 = WebSocketSequence(
        id="seq_login_flow",
        name="Login and Subscribe",
        steps=[seq_step1, seq_step2, seq_step3],
    )

    return WebSocketConnection(
        id="ws_composer_test",
        name="Composer Test Feed",
        url="wss://ws.example.com/v1/feed",
        presets=[p1, p2, p3],
        sequences=[seq1],
        default_format=WsMessageFormat.JSON,
    )


def _assert_widget_identity(widget: QObject, expected_id: str) -> None:
    """Helper verifying objectName and accessibleIdentifier."""
    name = widget.objectName()
    assert name == expected_id, f"Expected objectName '{expected_id}', got '{name}'"
    if isinstance(widget, QWidget):
        getter = getattr(widget, "accessibleIdentifier", None)
        if callable(getter):
            assert getter() == expected_id, (
                f"Expected accessibleIdentifier '{expected_id}', got '{getter()}'"
            )


# =============================================================================
# 1. Multi-Format Payload Composition & Pre-Send Validation
# =============================================================================


class TestMultiFormatPayloadCompositionAndValidation:
    """Tests payload formatting, syntax checks, and codec encoding across all 4 formats."""

    def test_format_validation_text_json_hex_base64(self, qapp):
        """Verify real-time format validation logic across Text, JSON, Hex, and Base64."""
        conn = _make_sample_connection_with_presets()
        presenter = WebSocketPresenter(conn, AppSettings())
        composer = WebSocketComposer(presenter=presenter)

        # 1. TEXT format: any UTF-8 is valid
        composer.set_format(WsMessageFormat.TEXT)
        composer.set_payload("Hello WebSocket 🌍")
        assert composer.is_payload_valid() is True
        assert composer.get_validation_error() is None

        # 2. JSON format: valid JSON
        composer.set_format(WsMessageFormat.JSON)
        composer.set_payload('{"op": "subscribe", "channel": "ticker"}')
        assert composer.is_payload_valid() is True

        # JSON format: invalid syntax
        composer.set_format(WsMessageFormat.JSON)
        composer.set_payload('{"op": "subscribe", invalid_json')
        assert composer.is_payload_valid() is False
        assert composer.get_validation_error() is not None

        # 3. HEX format: valid even-length hex string
        composer.set_format(WsMessageFormat.HEX)
        composer.set_payload("48656c6c6f")
        assert composer.is_payload_valid() is True

        # HEX format: invalid odd-length hex string
        composer.set_format(WsMessageFormat.HEX)
        composer.set_payload("48656c6c6")
        assert composer.is_payload_valid() is False
        assert "odd length" in composer.get_validation_error().lower()

        # HEX format: invalid non-hex characters
        composer.set_format(WsMessageFormat.HEX)
        composer.set_payload("48656c6cZZ")
        assert composer.is_payload_valid() is False

        # 4. BASE64 format: valid base64
        composer.set_format(WsMessageFormat.BASE64)
        composer.set_payload("SGVsbG8gV29ybGQ=")
        assert composer.is_payload_valid() is True

        # BASE64 format: invalid characters/padding
        composer.set_format(WsMessageFormat.BASE64)
        composer.set_payload("SGVsbG8$$$")
        assert composer.is_payload_valid() is False

    def test_composer_dispatches_text_vs_binary_to_controller(self, qapp):
        """Verify Text/JSON dispatch text frames while Hex/Base64 dispatch binary frames."""
        conn = _make_sample_connection_with_presets()
        presenter = WebSocketPresenter(conn, AppSettings())
        presenter._state = SessionState.OPEN  # Simulate open connection
        mock_controller = MagicMock()
        presenter._controller = mock_controller

        composer = WebSocketComposer(presenter=presenter)

        # Send JSON -> session_controller.send_text
        composer.set_format(WsMessageFormat.JSON)
        composer.set_payload('{"action": "ping"}')
        success = composer.send_current_payload()
        assert success is True
        mock_controller.send_text.assert_called_with('{"action": "ping"}')

        # Send HEX -> session_controller.send_binary with decoded bytes
        mock_controller.reset_mock()
        composer.set_format(WsMessageFormat.HEX)
        composer.set_payload("48656c6c6f")  # "Hello"
        success = composer.send_current_payload()
        assert success is True
        mock_controller.send_binary.assert_called_with(b"Hello")

        # Send BASE64 -> session_controller.send_binary with decoded bytes
        mock_controller.reset_mock()
        composer.set_format(WsMessageFormat.BASE64)
        composer.set_payload("SGVsbG8=")  # "Hello"
        success = composer.send_current_payload()
        assert success is True
        mock_controller.send_binary.assert_called_with(b"Hello")

    def test_composer_blocks_send_when_payload_invalid(self, qapp):
        """Verify invalid payload prevents transmission and does not call controller."""
        conn = _make_sample_connection_with_presets()
        presenter = WebSocketPresenter(conn, AppSettings())
        presenter._state = SessionState.OPEN
        mock_controller = MagicMock()
        presenter._controller = mock_controller

        composer = WebSocketComposer(presenter=presenter)
        composer.set_format(WsMessageFormat.JSON)
        composer.set_payload("{malformed json")

        success = composer.send_current_payload()
        assert success is False
        mock_controller.send_text.assert_not_called()
        mock_controller.send_binary.assert_not_called()


# =============================================================================
# 2. Preset CRUD, Persistence, Duplication & "Send Now"
# =============================================================================


class TestPresetCrudAndPersistence:
    """Tests message preset management, round-trip editing, and dispatch actions."""

    def test_preset_crud_and_persistence(self, qapp):
        """Verify creating, editing, and deleting presets updates connection data."""
        conn = _make_sample_connection_with_presets()
        presenter = WebSocketPresenter(conn, AppSettings())
        panel = WebSocketPresetsPanel(presenter=presenter)

        initial_count = len(conn.presets)

        # 1. Create new preset
        new_preset = panel.create_new_preset(
            name="New Echo",
            format=WsMessageFormat.TEXT,
            payload="echo test",
        )
        assert len(conn.presets) == initial_count + 1
        assert new_preset.name == "New Echo"

        # 2. Duplicate preset
        duplicated = panel.duplicate_preset(new_preset.id)
        assert duplicated.id != new_preset.id
        assert duplicated.name == "New Echo (Copy)"
        assert duplicated.payload == "echo test"
        assert len(conn.presets) == initial_count + 2

        # 3. Delete preset
        panel.delete_preset(duplicated.id)
        assert len(conn.presets) == initial_count + 1
        assert all(p.id != duplicated.id for p in conn.presets)

    def test_load_preset_into_composer(self, qapp):
        """Verify [Load into composer] populates composer format and payload."""
        conn = _make_sample_connection_with_presets()
        presenter = WebSocketPresenter(conn, AppSettings())
        composer = WebSocketComposer(presenter=presenter)
        panel = WebSocketPresetsPanel(presenter=presenter, composer=composer)

        target_preset = conn.presets[0]  # preset_auth: JSON, '{"action": "auth", ...}'
        panel.load_preset_into_composer(target_preset.id)

        assert composer.get_format() == target_preset.format
        assert composer.get_payload() == target_preset.payload

    def test_send_now_dispatches_without_mutating_composer_buffer(self, qapp):
        """Verify [Send now] transmits preset payload while preserving composer content."""
        conn = _make_sample_connection_with_presets()
        presenter = WebSocketPresenter(conn, AppSettings())
        presenter._state = SessionState.OPEN
        mock_controller = MagicMock()
        presenter._controller = mock_controller

        composer = WebSocketComposer(presenter=presenter)
        composer.set_payload("draft scratch payload in composer")

        panel = WebSocketPresetsPanel(presenter=presenter, composer=composer)
        preset_to_send = conn.presets[1]  # Heartbeat Ping: 'ping'

        success = panel.send_preset_now(preset_to_send.id)
        assert success is True
        mock_controller.send_text.assert_called_with("ping")

        # Composer content MUST remain untouched
        assert composer.get_payload() == "draft scratch payload in composer"

    def test_empty_presets_guidance_state(self, qapp):
        """Verify empty state guidance when connection has no presets."""
        conn = WebSocketConnection(id="ws_empty", name="Empty", url="wss://empty.test")
        presenter = WebSocketPresenter(conn, AppSettings())
        panel = WebSocketPresetsPanel(presenter=presenter)

        assert panel.has_presets() is False
        assert panel.get_empty_presets_notice() is not None


# =============================================================================
# 3. Sequence Plan Compilation & Validation
# =============================================================================


class TestSequencePlanCompilation:
    """Tests compilation of sequence definitions into executable step plans."""

    def test_compile_valid_sequence_plan(self):
        """Verify sequence plan compiles with mixed presets and inline payloads."""
        conn = _make_sample_connection_with_presets()
        seq = conn.sequences[0]

        plan: SequenceExecutionPlan = compile_sequence_plan(
            sequence=seq,
            presets=conn.presets,
        )

        assert plan.is_valid is True
        assert plan.validation_error is None
        assert plan.sequence_id == seq.id
        assert len(plan.steps) == 3

        # Step 0: Auth Login (preset)
        assert plan.steps[0].display_name == "Auth Login"
        assert plan.steps[0].format == WsMessageFormat.JSON
        assert plan.steps[0].delay_ms == 0

        # Step 1: Heartbeat Ping (preset)
        assert plan.steps[1].display_name == "Heartbeat Ping"
        assert plan.steps[1].format == WsMessageFormat.TEXT
        assert plan.steps[1].delay_ms == 100

        # Step 2: Inline step
        assert plan.steps[2].display_name == "<inline>"
        assert plan.steps[2].format == WsMessageFormat.TEXT
        assert plan.steps[2].raw_payload == "sub:trades"
        assert plan.steps[2].delay_ms == 250

    def test_compile_sequence_plan_missing_preset_blocks_plan(self):
        """Verify deleted or missing preset ID renders error and marks plan invalid."""
        conn = _make_sample_connection_with_presets()
        broken_step = WebSocketSequenceStep(preset_id="deleted_preset_999", delay_ms=50)
        broken_seq = WebSocketSequence(
            id="seq_broken",
            name="Broken Sequence",
            steps=[broken_step],
        )

        plan: SequenceExecutionPlan = compile_sequence_plan(
            sequence=broken_seq,
            presets=conn.presets,
        )

        assert plan.is_valid is False
        assert plan.validation_error is not None
        assert "deleted_preset_999" in plan.validation_error
        assert "<missing preset" in plan.steps[0].display_name

    def test_compile_sequence_plan_invalid_payload_format(self):
        """Verify inline step with invalid format (e.g. invalid hex) marks plan invalid."""
        conn = _make_sample_connection_with_presets()
        invalid_hex_step = WebSocketSequenceStep(
            inline_payload="123",  # Odd length hex
            format=WsMessageFormat.HEX,
            delay_ms=0,
        )
        seq = WebSocketSequence(
            id="seq_invalid_hex",
            name="Invalid Hex Step Seq",
            steps=[invalid_hex_step],
        )

        plan: SequenceExecutionPlan = compile_sequence_plan(
            sequence=seq,
            presets=conn.presets,
        )

        assert plan.is_valid is False
        assert plan.validation_error is not None
        assert "hex" in plan.validation_error.lower()


# =============================================================================
# 4. Asynchronous Qt Sequence Runner Execution & Controls
# =============================================================================


class TestSequenceRunnerAsyncExecution:
    """Tests non-blocking QTimer-paced sequence execution, cancellation, and error handling."""

    def test_sequence_runner_executes_steps_in_order_with_pacing(self, qapp):
        """Verify sequence runner executes steps in order and delivers frames to controller."""
        conn = _make_sample_connection_with_presets()
        seq = conn.sequences[0]
        plan = compile_sequence_plan(seq, conn.presets)

        mock_controller = MagicMock()
        mock_controller.is_open = True

        runner = WebSocketSequenceRunner()
        completed_steps: list[StepExecutionResult] = []
        final_outcome: Optional[SequenceRunOutcome] = None

        runner.step_completed.connect(lambda res: completed_steps.append(res))
        runner.sequence_finished.connect(lambda outcome: nonlocal_outcome_set(outcome))

        def nonlocal_outcome_set(outcome: SequenceRunOutcome) -> None:
            nonlocal final_outcome
            final_outcome = outcome

        runner.run_sequence(plan=plan, controller=mock_controller)

        # Spin Qt event loop until finished (or bounded timeout)
        deadline = time.time() + 5.0
        while final_outcome is None and time.time() < deadline:
            qapp.processEvents()
            time.sleep(0.01)

        assert final_outcome is not None
        assert final_outcome.status == "completed"
        assert final_outcome.executed_steps == 3
        assert len(completed_steps) == 3
        assert mock_controller.send_text.call_count >= 2

    def test_sequence_runner_stop_halts_execution_and_leaves_session_open(self, qapp):
        """Verify calling stop() mid-run cancels future steps without closing session."""
        conn = _make_sample_connection_with_presets()
        # Create sequence with long pacing delay
        step1 = WebSocketSequenceStep(
            inline_payload="step1",
            format=WsMessageFormat.TEXT,
            delay_ms=0,
        )
        step2 = WebSocketSequenceStep(
            inline_payload="step2",
            format=WsMessageFormat.TEXT,
            delay_ms=1000,
        )
        step3 = WebSocketSequenceStep(
            inline_payload="step3",
            format=WsMessageFormat.TEXT,
            delay_ms=1000,
        )
        seq = WebSocketSequence(id="seq_pacing", name="Paced Seq", steps=[step1, step2, step3])
        plan = compile_sequence_plan(seq, conn.presets)

        mock_controller = MagicMock()
        mock_controller.is_open = True

        runner = WebSocketSequenceRunner()
        final_outcome: Optional[SequenceRunOutcome] = None
        runner.sequence_finished.connect(lambda outcome: nonlocal_set(outcome))

        def nonlocal_set(outcome: SequenceRunOutcome) -> None:
            nonlocal final_outcome
            final_outcome = outcome

        runner.run_sequence(plan=plan, controller=mock_controller)

        # Allow step 1 to execute
        qapp.processEvents()
        time.sleep(0.05)
        qapp.processEvents()

        # Stop runner during step 2 delay
        runner.stop()

        deadline = time.time() + 2.0
        while final_outcome is None and time.time() < deadline:
            qapp.processEvents()
            time.sleep(0.01)

        assert final_outcome is not None
        assert final_outcome.status == "stopped"
        assert final_outcome.executed_steps < 3
        # Controller close must NOT have been triggered
        mock_controller.disconnect.assert_not_called()
        mock_controller.close.assert_not_called()

    def test_sequence_runner_halts_on_step_failure(self, qapp):
        """Verify runner halts immediately when controller fails during step dispatch."""
        conn = _make_sample_connection_with_presets()
        seq = conn.sequences[0]
        plan = compile_sequence_plan(seq, conn.presets)

        mock_controller = MagicMock()
        mock_controller.is_open = True
        mock_controller.send_text.side_effect = RuntimeError("Socket write fault")

        runner = WebSocketSequenceRunner()
        final_outcome: Optional[SequenceRunOutcome] = None
        runner.sequence_finished.connect(lambda outcome: nonlocal_set(outcome))

        def nonlocal_set(outcome: SequenceRunOutcome) -> None:
            nonlocal final_outcome
            final_outcome = outcome

        runner.run_sequence(plan=plan, controller=mock_controller)

        deadline = time.time() + 2.0
        while final_outcome is None and time.time() < deadline:
            qapp.processEvents()
            time.sleep(0.01)

        assert final_outcome is not None
        assert final_outcome.status == "failed"
        assert "Socket write fault" in str(final_outcome.failure_reason)


# =============================================================================
# 5. Messages Sub-Tab Master/Detail UI & Empty States
# =============================================================================


class TestMessagesSubTabMasterDetailUI:
    """Tests the Messages sub-tab hosting Presets and Sequences master/detail panels."""

    def test_messages_tab_is_embedded_in_connection_editor_detail_tabs(self, qapp):
        """Verify Messages sub-tab is registered in WS_DETAIL_TABS with identity WS_MESSAGES_TAB."""
        conn = _make_sample_connection_with_presets()
        presenter = WebSocketPresenter(conn, AppSettings())
        tab = WebSocketTab(conn, presenter)

        detail_tabs = tab.findChild(QTabWidget, widget_ids.WS_DETAIL_TABS)
        assert detail_tabs is not None

        messages_tab = tab.findChild(QWidget, widget_ids.WS_MESSAGES_TAB)
        assert messages_tab is not None

    def test_sequence_steps_table_reordering_and_editing(self, qapp):
        """Verify steps table supports Add, Remove, Move Up, and Move Down actions."""
        conn = _make_sample_connection_with_presets()
        presenter = WebSocketPresenter(conn, AppSettings())
        panel = WebSocketPresetsPanel(presenter=presenter)

        seq = conn.sequences[0]
        panel.select_sequence(seq.id)

        initial_step_count = len(seq.steps)
        assert initial_step_count == 3

        # Add new inline step
        panel.add_sequence_step(
            seq.id,
            inline_payload="new step",
            format=WsMessageFormat.TEXT,
            delay_ms=150,
        )
        assert len(seq.steps) == initial_step_count + 1

        # Move last step up
        panel.move_sequence_step_up(seq.id, step_index=len(seq.steps) - 1)
        assert seq.steps[-2].inline_payload == "new step"

        # Move step down
        panel.move_sequence_step_down(seq.id, step_index=len(seq.steps) - 2)
        assert seq.steps[-1].inline_payload == "new step"

        # Remove step
        panel.remove_sequence_step(seq.id, step_index=len(seq.steps) - 1)
        assert len(seq.steps) == initial_step_count


# =============================================================================
# 6. Disconnected Session Guards
# =============================================================================


class TestDisconnectedSessionRefusal:
    """Tests send/run refusal when WebSocket session is not in SessionState.OPEN."""

    def test_composer_send_refused_when_disconnected(self, qapp):
        """Verify sending from composer while disconnected is refused without calling controller."""
        conn = _make_sample_connection_with_presets()
        presenter = WebSocketPresenter(conn, AppSettings())
        presenter._state = SessionState.IDLE
        mock_controller = MagicMock()
        presenter._controller = mock_controller

        composer = WebSocketComposer(presenter=presenter)
        composer.set_payload("test")
        success = composer.send_current_payload()

        assert success is False
        mock_controller.send_text.assert_not_called()
        mock_controller.send_binary.assert_not_called()

    def test_preset_send_now_refused_when_disconnected(self, qapp):
        """Verify Send now on preset while disconnected is refused."""
        conn = _make_sample_connection_with_presets()
        presenter = WebSocketPresenter(conn, AppSettings())
        presenter._state = SessionState.CONNECTING
        mock_controller = MagicMock()
        presenter._controller = mock_controller

        panel = WebSocketPresetsPanel(presenter=presenter)
        success = panel.send_preset_now(conn.presets[0].id)

        assert success is False
        mock_controller.send_text.assert_not_called()

    def test_sequence_run_refused_when_disconnected(self, qapp):
        """Verify running a sequence while disconnected is refused."""
        conn = _make_sample_connection_with_presets()
        presenter = WebSocketPresenter(conn, AppSettings())
        presenter._state = SessionState.IDLE

        panel = WebSocketPresetsPanel(presenter=presenter)
        started = panel.run_sequence(conn.sequences[0].id)

        assert started is False


# =============================================================================
# 7. Automation Widget Identities Spot-Check
# =============================================================================


class TestAutomationWidgetIdentities:
    """Tests all WS-6 automation identities defined in widget_ids.py on live widgets."""

    def test_widget_identity_constants_declared(self):
        """Verify all WS-6 automation identity constants exist in widget_ids."""
        expected_constants = [
            "WS_COMPOSER_FORMAT_COMBO",
            "WS_PRESET_COMBO",
            "WS_PRESET_SAVE_BUTTON",
            "WS_SEQUENCE_COMBO",
            "WS_SEQUENCE_RUN_BUTTON",
            "WS_SEQUENCE_STOP_BUTTON",
            "WS_MESSAGES_TAB",
            "WS_PRESETS_LIST",
            "WS_PRESET_NAME_INPUT",
            "WS_PRESET_FORMAT_COMBO",
            "WS_PRESET_PAYLOAD_EDIT",
            "WS_PRESET_NEW_BUTTON",
            "WS_PRESET_DUPLICATE_BUTTON",
            "WS_PRESET_DELETE_BUTTON",
            "WS_PRESET_LOAD_BUTTON",
            "WS_PRESET_SEND_BUTTON",
            "WS_SEQUENCES_LIST",
            "WS_SEQUENCE_NEW_BUTTON",
            "WS_SEQUENCE_DUPLICATE_BUTTON",
            "WS_SEQUENCE_DELETE_BUTTON",
            "WS_SEQUENCE_STEPS_TABLE",
            "WS_SEQUENCE_STEP_ADD_BUTTON",
            "WS_SEQUENCE_STEP_REMOVE_BUTTON",
            "WS_SEQUENCE_STEP_UP_BUTTON",
            "WS_SEQUENCE_STEP_DOWN_BUTTON",
        ]
        for const_name in expected_constants:
            assert hasattr(widget_ids, const_name), f"widget_ids missing {const_name}"
            val = getattr(widget_ids, const_name)
            assert isinstance(val, str)
            assert val.startswith("pypost_ws_")
            assert val in widget_ids.KEY_WIDGET_IDS

    def test_live_widget_instances_expose_identities(self, qapp):
        """Verify widgets created in Composer and PresetsPanel expose their identities."""
        conn = _make_sample_connection_with_presets()
        presenter = WebSocketPresenter(conn, AppSettings())
        tab = WebSocketTab(conn, presenter)

        composer = tab.findChild(WebSocketComposer)
        assert composer is not None

        presets_panel = tab.findChild(WebSocketPresetsPanel)
        assert presets_panel is not None

        # Check composer controls
        format_combo = composer.findChild(QComboBox, widget_ids.WS_COMPOSER_FORMAT_COMBO)
        assert format_combo is not None
        _assert_widget_identity(format_combo, widget_ids.WS_COMPOSER_FORMAT_COMBO)

        preset_combo = composer.findChild(QComboBox, widget_ids.WS_PRESET_COMBO)
        assert preset_combo is not None
        _assert_widget_identity(preset_combo, widget_ids.WS_PRESET_COMBO)

        save_btn = composer.findChild(QPushButton, widget_ids.WS_PRESET_SAVE_BUTTON)
        assert save_btn is not None
        _assert_widget_identity(save_btn, widget_ids.WS_PRESET_SAVE_BUTTON)

        seq_combo = composer.findChild(QComboBox, widget_ids.WS_SEQUENCE_COMBO)
        assert seq_combo is not None
        _assert_widget_identity(seq_combo, widget_ids.WS_SEQUENCE_COMBO)

        run_btn = composer.findChild(QPushButton, widget_ids.WS_SEQUENCE_RUN_BUTTON)
        assert run_btn is not None
        _assert_widget_identity(run_btn, widget_ids.WS_SEQUENCE_RUN_BUTTON)

        stop_btn = composer.findChild(QPushButton, widget_ids.WS_SEQUENCE_STOP_BUTTON)
        assert stop_btn is not None
        _assert_widget_identity(stop_btn, widget_ids.WS_SEQUENCE_STOP_BUTTON)


# =============================================================================
# 8. Observability and Structured Logging Tests (PYPOST-1134 / WS-6)
# =============================================================================


class TestWebSocketObservabilityLogging:
    """Caplog-driven assertions validating structured logging across WS-6 components."""

    def test_composer_format_validation_and_dispatch_logging(self, qapp, caplog):
        """Verify WebSocketComposer emits structured logs on validation failures and dispatch."""
        composer = WebSocketComposer()
        secret_content = "super_secret_payload_token_xyz123"

        with caplog.at_level(logging.DEBUG, logger="pypost.ui.widgets.websocket.composer"):
            # Trigger JSON format validation failure
            composer.set_format(WsMessageFormat.JSON)
            composer.set_payload("{ invalid_json: true ")

            # Attempt send while disconnected
            res = composer.send_current_payload()
            assert res is False

            # Set valid payload and mock open presenter
            composer.set_format(WsMessageFormat.TEXT)
            composer.set_payload(secret_content)

            mock_presenter = MagicMock()
            mock_presenter.state = SessionState.OPEN
            mock_presenter._current_state = SessionState.OPEN
            mock_presenter.connection = WebSocketConnection(id="c1", name="Test")
            mock_controller = MagicMock()
            mock_presenter._controller = mock_controller
            composer.presenter = mock_presenter

            sent = composer.send_current_payload()
            assert sent is True

        records = [r for r in caplog.records if r.name == "pypost.ui.widgets.websocket.composer"]
        messages = [r.getMessage() for r in records]

        # Verify format validation failure was logged as warning
        assert any("composer_format_validation_failed" in msg and "format=json" in msg for msg in messages)

        # Verify dispatch log emitted
        assert any("composer_payload_dispatched" in msg and "format=text" in msg and f"bytes={len(secret_content)}" in msg for msg in messages)

        # Verify raw sensitive payload string is NOT leaked into log records
        for msg in messages:
            assert secret_content not in msg

    def test_sequence_compilation_logging(self, caplog):
        """Verify compile_sequence_plan emits structured logs for planning and errors."""
        seq = WebSocketSequence(
            id="seq_test_obs",
            name="Obs Sequence",
            steps=[
                WebSocketSequenceStep(preset_id="preset_missing", delay_ms=50),
                WebSocketSequenceStep(inline_payload="not valid json", format=WsMessageFormat.JSON),
            ],
        )

        with caplog.at_level(logging.DEBUG, logger="pypost.core.websocket_sequence"):
            plan = compile_sequence_plan(seq, [])
            assert plan.is_valid is False

        records = [r for r in caplog.records if r.name == "pypost.core.websocket_sequence"]
        messages = [r.getMessage() for r in records]

        assert any("compile_sequence_plan_started" in msg and "seq_id=seq_test_obs" in msg for msg in messages)
        assert any("compile_sequence_plan_missing_preset" in msg and "preset_id=preset_missing" in msg for msg in messages)
        assert any("compile_sequence_plan_step_invalid" in msg and "format=json" in msg for msg in messages)
        assert any("compile_sequence_plan_completed" in msg and "is_valid=False" in msg for msg in messages)

    def test_sequence_runner_execution_and_stop_logging(self, qapp, caplog):
        """Verify WebSocketSequenceRunner emits structured logs across lifecycle events."""
        p1 = WebSocketMessagePreset(id="p1", name="Step1", format=WsMessageFormat.TEXT, payload="hello")
        seq = WebSocketSequence(
            id="seq_run_obs",
            name="Run Obs",
            steps=[WebSocketSequenceStep(preset_id="p1", delay_ms=0)],
        )
        plan = compile_sequence_plan(seq, [p1])

        mock_controller = MagicMock()
        mock_controller.is_open = True

        runner = WebSocketSequenceRunner()

        with caplog.at_level(logging.DEBUG, logger="pypost.core.qt.websocket_sequence_runner"):
            # Test rejected invalid plan
            invalid_plan = SequenceExecutionPlan(
                sequence_id="seq_inv",
                sequence_name="Invalid",
                steps=(),
                is_valid=False,
                validation_error="Invalid plan structure",
            )
            runner.run_sequence(invalid_plan, mock_controller)

            # Test run valid plan
            started = runner.run_sequence(plan, mock_controller)
            assert started is True

            # Allow zero-delay step to execute
            time.sleep(0.01)
            qapp.processEvents()

            # Test stop logging
            runner._is_running = True
            runner._plan = plan
            runner.stop()

        records = [r for r in caplog.records if r.name == "pypost.core.qt.websocket_sequence_runner"]
        messages = [r.getMessage() for r in records]

        assert any("sequence_runner_rejected_invalid_plan" in msg and "seq_id=seq_inv" in msg for msg in messages)
        assert any("sequence_runner_started" in msg and "seq_id=seq_run_obs" in msg for msg in messages)
        assert any("sequence_runner_step_executed" in msg and "name=Step1" in msg for msg in messages)
        assert any("sequence_runner_completed" in msg and "seq_id=seq_run_obs" in msg for msg in messages)
        assert any("sequence_runner_stopped_by_user" in msg and "seq_id=seq_run_obs" in msg for msg in messages)

    def test_presets_panel_crud_and_send_logging(self, qapp, caplog):
        """Verify WebSocketPresetsPanel emits structured logs for CRUD actions and direct send."""
        conn = WebSocketConnection(id="conn_obs", name="Observability Test")
        presenter = WebSocketPresenter(conn, AppSettings())
        presenter._current_state = SessionState.OPEN
        panel = WebSocketPresetsPanel(presenter=presenter)

        with caplog.at_level(logging.INFO, logger="pypost.ui.widgets.websocket.presets_panel"):
            # Create preset
            preset = panel.create_new_preset(name="My Auth", format=WsMessageFormat.TEXT, payload="token:secret123")
            preset_id = preset.id

            # Duplicate preset
            dup = panel.duplicate_preset(preset_id)

            # Load into composer
            composer = WebSocketComposer(presenter=presenter)
            panel.composer = composer
            panel.load_preset_into_composer(preset_id)

            # Create sequence & add step
            panel._on_seq_new_clicked()
            seq_id = panel._selected_sequence_id
            assert seq_id is not None
            panel.add_sequence_step(seq_id, preset_id=preset_id, format=WsMessageFormat.TEXT, delay_ms=50)

            # Remove step
            panel.remove_sequence_step(seq_id, 0)

            # Delete preset
            panel.delete_preset(dup.id)

        records = [r for r in caplog.records if r.name == "pypost.ui.widgets.websocket.presets_panel"]
        messages = [r.getMessage() for r in records]

        assert any("preset_created" in msg and "name=My Auth" in msg for msg in messages)
        assert any("preset_duplicated" in msg and "name=My Auth (Copy)" in msg for msg in messages)
        assert any("preset_loaded_into_composer" in msg and "name=My Auth" in msg for msg in messages)
        assert any("sequence_created" in msg for msg in messages)
        assert any("sequence_step_added" in msg and f"seq_id={seq_id}" in msg for msg in messages)
        assert any("sequence_step_removed" in msg and f"seq_id={seq_id}" in msg for msg in messages)
        assert any("preset_deleted" in msg and f"preset_id={dup.id}" in msg for msg in messages)

        # Assert secret payload text is NOT logged in full
        for msg in messages:
            assert "token:secret123" not in msg
