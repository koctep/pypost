"""Failing repro tests for WS-9 Bounded MCP WebSocket probe tool.

Task: PYPOST-1137.
Asserts the contract and behavior specified in:
- `ai-tasks/PYPOST-1137/10-requirements.md`
- `ai-tasks/PYPOST-1137/20-architecture.md`

Covers:
1. Tool Schema & Parameter Isolation (`list_tools`):
   - Exposed WebSocket profiles generate tools named `ws_<normalized_name>`.
   - Tool schema inputSchema extracts ONLY `mcp.request.*` variables.
   - Hidden keys and environment-only variables are strictly excluded from tool schemas.
   - Optional `stop_when` string parameter is present in schemas.
   - Unexposed WebSocket profiles are not published to `list_tools`.
2. Probe Limits & Global Ceilings:
   - Profile overrides for `mcp_probe_max_messages` and `mcp_probe_max_duration_ms`
     are clamped to global ceilings configured in `AppSettings`.
3. Stop Conditions:
   - Bounded by message count reaching effective limit (`limit_reached`).
   - Bounded by elapsed duration reaching timeout (`timeout`).
   - Bounded by incoming message substring match (`stop_when_matched`).
4. Probe Execution & Sanitized Transcript:
   - Connects to endpoint, sends designated preset payload on open.
   - Collects frames and closes with WebSocket code 1000 ("probe complete").
   - Output transcript is sanitized with `sanitize_text`, masking secrets as `***`.
5. Thread Safety & Lifecycle Guarantees:
   - `WebSocketProbeRunner` (QThread) runs on a dedicated event loop with hard deadline timer.
   - Runner thread terminates cleanly and never outlives the probe call (isFinished == True).
6. Concurrency Slot Governance (`SessionSlots`):
   - Probe acquires a slot on start and releases on all exit paths.
   - When `SessionSlots` active count reaches `ws_max_concurrent_sessions`, returns
     informative refusal notice without opening socket.
7. MCPServerImpl Integration:
   - Tool registration accepts WebSocket connections alongside HTTP requests.
   - `list_tools` and `call_tool` dispatch WebSocket probes end-to-end.
8. Daemon Storage Snapshot Loading:
   - `load_collections_snapshot_strict` loads `Collection.websockets` under headless daemon.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
import uuid
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QCoreApplication
from PySide6.QtWebSockets import QWebSocket

from pypost.core.daemon_storage import load_collections_snapshot_strict
from pypost.core.mcp_server_impl import MCPServerImpl
from pypost.core.qt.websocket_probe_runner import WebSocketProbeRunner
from pypost.core.qt.websocket_probe_executor import execute_qt_websocket_probe
from pypost.core.template_service import TemplateService
from pypost.core.websocket_mcp_tools import (
    build_websocket_mcp_preview,
    build_websocket_mcp_tool_schema,
    execute_websocket_probe,
    extract_websocket_mcp_variables,
)
from pypost.core.websocket_probe import (
    ProbeEvent,
    ProbeOutcome,
    WebSocketProbeConfig,
    WebSocketProbeResult,
    WebSocketProbeStopCondition,
    calculate_effective_probe_limits,
    format_probe_transcript,
)
from pypost.core.websocket_session_policy import get_session_slots
from pypost.core.websocket_transport_protocol import HandshakeTarget
from pypost.models.models import Collection, McpToolParam, RequestData
from pypost.models.settings import AppSettings
from pypost.models.websocket import (
    WebSocketConnection,
    WebSocketMessagePreset,
)
from tests.helpers.process_until import process_until
from tests.websocket_echo_server import (
    ScriptedWebSocketServer,
    ServerBehavior,
    ServerBehaviorConfig,
)

pytestmark = pytest.mark.timeout(30)


# =============================================================================
# 1. Tool Schema & Parameter Isolation Tests
# =============================================================================


class TestWebSocketMcpToolSchemaAndIsolation:
    """Asserts schema generation and parameter isolation rules for WebSocket MCP tools."""

    def test_extract_websocket_mcp_variables(self) -> None:
        """Extracts only mcp.request.* placeholders from URL, headers, params, and preset."""
        preset = WebSocketMessagePreset(
            id="preset-1",
            name="Subscribe",
            payload=(
                '{"action": "sub", "channel": "{{mcp.request.channel}}", '
                '"token": "{{SECRET_KEY}}"}'
            ),
        )
        conn = WebSocketConnection(
            name="Crypto Stream",
            url="wss://stream.example.com/ws?market={{mcp.request.market}}&auth={{ENV_AUTH}}",
            headers={
                "X-Client-ID": "{{mcp.request.client_id}}",
                "Authorization": "Bearer {{SECRET_TOKEN}}",
            },
            params={"interval": "{{mcp.request.timeframe}}", "static": "fixed"},
            mcp_probe_preset_id="preset-1",
            presets=[preset],
        )

        vars_found = extract_websocket_mcp_variables(conn)
        assert vars_found == {"market", "client_id", "timeframe", "channel"}
        assert "SECRET_KEY" not in vars_found
        assert "ENV_AUTH" not in vars_found
        assert "SECRET_TOKEN" not in vars_found

    def test_build_websocket_mcp_tool_schema_strips_hidden_keys(self) -> None:
        """Schema includes mcp.request params + stop_when, while stripping hidden keys."""
        preset = WebSocketMessagePreset(
            id="preset-1",
            name="Init",
            payload='{"token": "{{mcp.request.api_key}}", "topic": "{{mcp.request.topic}}"}',
        )
        conn = WebSocketConnection(
            name="Telemetry Stream",
            expose_as_mcp=True,
            url="ws://telemetry.local/ws",
            mcp_probe_preset_id="preset-1",
            presets=[preset],
            mcp_params={
                "api_key": McpToolParam(description="API Key", required=True),
                "topic": McpToolParam(description="Telemetry Topic", required=True),
            },
        )

        # api_key is in hidden_keys -> must be stripped from inputSchema
        hidden_keys = {"api_key"}
        schema = build_websocket_mcp_tool_schema(conn, TemplateService(), hidden_keys)

        assert "properties" in schema
        assert "topic" in schema["properties"]
        assert "api_key" not in schema["properties"]
        assert "stop_when" in schema["properties"]
        assert schema["properties"]["stop_when"]["type"] == "string"
        assert "topic" in schema.get("required", [])
        assert "api_key" not in schema.get("required", [])

    def test_build_websocket_mcp_preview(self) -> None:
        """Generates MCP tool preview with normalized tool name and contract details."""
        conn = WebSocketConnection(
            name="Binance BTC/USDT Feed",
            expose_as_mcp=True,
            mcp_description="Stream real-time trade ticks for BTC/USDT",
            url="wss://stream.binance.com/ws",
        )
        preview = build_websocket_mcp_preview(conn)
        assert preview is not None
        assert preview.tool_name == "ws_binance_btc_usdt_feed"
        assert preview.description == "Stream real-time trade ticks for BTC/USDT"
        assert "properties" in preview.input_schema
        assert "stop_when" in preview.input_schema["properties"]

    def test_build_websocket_mcp_preview_returns_none_when_unexposed(self) -> None:
        """Returns None if expose_as_mcp is False."""
        conn = WebSocketConnection(
            name="Private Stream",
            expose_as_mcp=False,
            url="wss://stream.example.com/ws",
        )
        assert build_websocket_mcp_preview(conn) is None


# =============================================================================
# 2. Probe Limits & Global Ceilings Tests
# =============================================================================


class TestWebSocketProbeLimitsAndCeilings:
    """Asserts effective probe limits calculation respects global AppSettings ceilings."""

    def test_calculate_effective_probe_limits_default(self) -> None:
        """Defaults to AppSettings ceilings when no profile overrides are set."""
        settings = AppSettings(
            ws_mcp_probe_max_messages=15,
            ws_mcp_probe_max_duration_ms=12000,
        )
        conn = WebSocketConnection(name="Default Limits", url="ws://127.0.0.1")

        eff_msgs, eff_dur = calculate_effective_probe_limits(conn, settings)
        assert eff_msgs == 15
        assert eff_dur == 12000

    def test_calculate_effective_probe_limits_profile_override_lower(self) -> None:
        """Allows per-profile overrides to lower the limits below global ceilings."""
        settings = AppSettings(
            ws_mcp_probe_max_messages=20,
            ws_mcp_probe_max_duration_ms=15000,
        )
        conn = WebSocketConnection(
            name="Quick Probe",
            url="ws://127.0.0.1",
            mcp_probe_max_messages=5,
            mcp_probe_max_duration_ms=3000,
        )

        eff_msgs, eff_dur = calculate_effective_probe_limits(conn, settings)
        assert eff_msgs == 5
        assert eff_dur == 3000

    def test_calculate_effective_probe_limits_clamps_to_global_ceiling(self) -> None:
        """Clamps per-profile overrides if they attempt to exceed global operator ceilings."""
        settings = AppSettings(
            ws_mcp_probe_max_messages=10,
            ws_mcp_probe_max_duration_ms=8000,
        )
        conn = WebSocketConnection(
            name="Greedy Probe",
            url="ws://127.0.0.1",
            mcp_probe_max_messages=500,  # Exceeds 10
            mcp_probe_max_duration_ms=120000,  # Exceeds 8000
        )

        eff_msgs, eff_dur = calculate_effective_probe_limits(conn, settings)
        assert eff_msgs == 10
        assert eff_dur == 8000


# =============================================================================
# 3. Stop Conditions & Transcript Formatting Tests
# =============================================================================


class TestWebSocketProbeStopConditions:
    """Asserts deterministic stopping conditions and transcript formatting."""

    def test_stop_condition_message_limit_reached(self) -> None:
        """Evaluates message count stop condition."""
        stop_cond = WebSocketProbeStopCondition(max_messages=2, stop_when=None)
        stop1, outcome1 = stop_cond.should_stop("message 1")
        assert not stop1
        assert outcome1 is None

        stop2, outcome2 = stop_cond.should_stop("message 2")
        assert stop2
        assert outcome2 == ProbeOutcome.LIMIT_REACHED

    def test_stop_condition_substring_match(self) -> None:
        """Evaluates early termination when stop_when substring is matched."""
        stop_cond = WebSocketProbeStopCondition(max_messages=10, stop_when="STATUS:READY")
        stop1, outcome1 = stop_cond.should_stop("STATUS:BOOTING")
        assert not stop1
        assert outcome1 is None

        stop2, outcome2 = stop_cond.should_stop('{"event": "update", "info": "STATUS:READY now"}')
        assert stop2
        assert outcome2 == ProbeOutcome.STOP_WHEN_MATCHED

    def test_format_probe_transcript_masks_secrets(self) -> None:
        """Transcript formatter redacts environment variables and hidden keys."""
        events = [
            ProbeEvent(
                timestamp_iso="2026-08-23T12:00:00Z",
                direction="connect",
                payload="Connected to ws://example.com?secret_token=super_secret_val",
            ),
            ProbeEvent(
                timestamp_iso="2026-08-23T12:00:01Z",
                direction="sent",
                payload='{"auth": "super_secret_val", "type": "sub"}',
            ),
            ProbeEvent(
                timestamp_iso="2026-08-23T12:00:02Z",
                direction="received",
                payload='{"status": "ok", "key": "hidden_api_key_123"}',
            ),
            ProbeEvent(
                timestamp_iso="2026-08-23T12:00:03Z",
                direction="closed",
                payload="Code: 1000, Reason: probe complete",
            ),
        ]
        result = WebSocketProbeResult(
            outcome=ProbeOutcome.LIMIT_REACHED,
            messages_received=1,
            duration_ms=123.4,
            events=events,
            close_code=1000,
            close_reason="probe complete",
        )

        env_vars = {"TOKEN": "super_secret_val"}
        hidden_keys = {"hidden_api_key_123"}
        transcript = format_probe_transcript(result, env_vars=env_vars, hidden_keys=hidden_keys)

        assert "=== WebSocket Probe Transcript ===" in transcript
        assert "Outcome: limit_reached" in transcript
        assert "super_secret_val" not in transcript
        assert "hidden_api_key_123" not in transcript
        assert "***" in transcript


# =============================================================================
# 4. Probe Execution & Bounded Sampling (Live QWebSocket & Echo Server)
# =============================================================================


class TestWebSocketProbeExecutionAndSanitization:
    """Asserts live bounded probe execution with ScriptedWebSocketServer."""

    def test_probe_bounded_by_message_count(self, ws_test_server) -> None:
        """Probe connects, sends preset, collects max_messages, closes with 1000."""
        # Configure server to echo messages
        ws_test_server.configure(ServerBehaviorConfig(behavior=ServerBehavior.ECHO))

        preset = WebSocketMessagePreset(
            id="preset-sub",
            name="Subscribe",
            payload='{"action": "ping", "id": "{{mcp.request.req_id}}"}',
        )
        conn = WebSocketConnection(
            name="Echo Feed",
            expose_as_mcp=True,
            url=ws_test_server.url,
            mcp_probe_preset_id="preset-sub",
            presets=[preset],
            mcp_probe_max_messages=1,
            mcp_probe_max_duration_ms=5000,
        )

        contents = execute_websocket_probe(
            conn,
            arguments={"req_id": "probe-42"},
            env_vars={},
            hidden_keys=set(),
            settings=AppSettings(),
            runner_factory=WebSocketProbeRunner,
            process_events=QCoreApplication.processEvents,
        )

        assert len(contents) == 1
        transcript = contents[0].text
        assert "=== WebSocket Probe Transcript ===" in transcript
        assert "Outcome: limit_reached" in transcript or "Outcome: success" in transcript
        assert "probe-42" in transcript
        assert "Code: 1000" in transcript

    def test_probe_bounded_by_stop_when(self, ws_test_server) -> None:
        """Probe stops immediately upon receiving message matching stop_when substring."""
        # Configure custom callback to emit multiple messages
        def custom_cb(server: ScriptedWebSocketServer, client: QWebSocket, msg: str) -> None:
            server.send_to_all("MSG 1: Starting")
            server.send_to_all("MSG 2: TARGET_EVENT_FOUND in stream")
            server.send_to_all("MSG 3: Trailing noise")

        ws_test_server.configure(
            ServerBehaviorConfig(
                behavior=ServerBehavior.CUSTOM_CALLBACK,
                custom_callback=custom_cb,
            )
        )

        conn = WebSocketConnection(
            name="Stream with Target",
            expose_as_mcp=True,
            url=ws_test_server.url,
            mcp_probe_max_messages=10,
            mcp_probe_max_duration_ms=5000,
        )

        preset = WebSocketMessagePreset(
            id="preset-start",
            name="Start",
            payload="start",
        )
        conn.presets = [preset]
        conn.mcp_probe_preset_id = "preset-start"

        contents = execute_websocket_probe(
            conn,
            arguments={"stop_when": "TARGET_EVENT_FOUND"},
            env_vars={},
            hidden_keys=set(),
            settings=AppSettings(),
            runner_factory=WebSocketProbeRunner,
            process_events=QCoreApplication.processEvents,
        )

        assert len(contents) == 1
        transcript = contents[0].text
        assert "Outcome: stop_when_matched" in transcript
        assert "TARGET_EVENT_FOUND" in transcript
        assert "MSG 3: Trailing noise" not in transcript

    def test_probe_bounded_by_duration_timeout(self, ws_test_server) -> None:
        """Probe stops with outcome timeout when server does not emit enough messages."""
        # Server accepts connections but stays silent
        ws_test_server.configure(ServerBehaviorConfig(behavior=ServerBehavior.SILENT))

        conn = WebSocketConnection(
            name="Silent Stream",
            expose_as_mcp=True,
            url=ws_test_server.url,
            mcp_probe_max_messages=10,
            mcp_probe_max_duration_ms=300,  # Short timeout
        )

        contents = execute_websocket_probe(
            conn,
            arguments={},
            env_vars={},
            hidden_keys=set(),
            settings=AppSettings(ws_mcp_probe_max_duration_ms=500),
            runner_factory=WebSocketProbeRunner,
            process_events=QCoreApplication.processEvents,
        )

        assert len(contents) == 1
        transcript = contents[0].text
        assert "Outcome: timeout" in transcript


# =============================================================================
# 5. Thread Safety & Lifecycle Guarantees
# =============================================================================


class TestWebSocketProbeRunnerThreadSafetyAndLifecycle:
    """Asserts WebSocketProbeRunner thread invariants and clean termination."""

    def test_runner_thread_always_terminates(self, ws_test_server) -> None:
        """Runner thread is finished and not running after execution completes."""
        ws_test_server.configure(ServerBehaviorConfig(behavior=ServerBehavior.ECHO))

        target = HandshakeTarget(url=ws_test_server.url)
        config = WebSocketProbeConfig(
            target=target,
            initial_payload="hello",
            max_messages=1,
            max_duration_ms=2000,
        )

        runner = WebSocketProbeRunner(config)
        runner.start()
        process_until(lambda: runner.isFinished(), timeout_ms=3000)

        assert runner.isFinished()
        assert not runner.isRunning()
        assert runner.result is not None
        assert runner.result.outcome in (ProbeOutcome.LIMIT_REACHED, ProbeOutcome.SUCCESS)

    def test_runner_thread_terminates_on_server_error(self) -> None:
        """Runner terminates cleanly when connection cannot be established."""
        # Point to an unreachable closed port
        target = HandshakeTarget(url="ws://127.0.0.1:1")
        config = WebSocketProbeConfig(
            target=target,
            max_messages=1,
            max_duration_ms=1000,
        )

        runner = WebSocketProbeRunner(config)
        runner.start()
        runner.wait(2000)

        assert runner.isFinished()
        assert not runner.isRunning()
        assert runner.result is not None
        assert runner.result.outcome == ProbeOutcome.ERROR


# =============================================================================
# 6. SessionSlots Concurrency Governance & Refusal
# =============================================================================


class TestWebSocketProbeSessionSlotsConcurrency:
    """Asserts SessionSlots allocation, release, and refusal under concurrency limits."""

    def test_probe_takes_and_releases_session_slot(self, ws_test_server) -> None:
        """Probe acquires a slot during execution and releases it afterwards."""
        slots = get_session_slots()
        initial_active = slots.active_count

        ws_test_server.configure(ServerBehaviorConfig(behavior=ServerBehavior.ECHO))
        target = HandshakeTarget(url=ws_test_server.url)
        config = WebSocketProbeConfig(
            target=target,
            initial_payload="ping",
            max_messages=1,
            max_duration_ms=2000,
        )

        runner = WebSocketProbeRunner(config)
        runner.start()
        process_until(lambda: runner.isFinished(), timeout_ms=3000)

        assert runner.isFinished()
        assert slots.active_count == initial_active

    def test_probe_returns_refusal_when_slots_full(self) -> None:
        """When SessionSlots is full, probe returns refusal without socket connection."""
        slots = get_session_slots()
        # Acquire all available slots
        acquired_ids = []
        try:
            while True:
                sid = str(uuid.uuid4())
                res = slots.acquire(sid)
                if not res.allowed:
                    break
                acquired_ids.append(sid)

            assert slots.is_full

            target = HandshakeTarget(url="ws://127.0.0.1:9999")
            config = WebSocketProbeConfig(
                target=target,
                max_messages=1,
                max_duration_ms=1000,
            )

            runner = WebSocketProbeRunner(config)
            runner.start()
            runner.wait(2000)

            assert runner.isFinished()
            assert runner.result is not None
            assert runner.result.outcome == ProbeOutcome.REFUSED
            assert "session limit reached" in (runner.result.error_message or "").lower()
        finally:
            for sid in acquired_ids:
                slots.release(sid)


# =============================================================================
# 7. MCPServerImpl End-to-End WebSocket Integration
# =============================================================================


class TestMCPServerImplWebSocketIntegration:
    """Asserts MCPServerImpl registration, listing, and dispatching of WebSocket tools."""

    def test_invalid_declared_value_does_not_invoke_websocket_probe(self) -> None:
        conn = WebSocketConnection(
            name="Typed Feed",
            expose_as_mcp=True,
            url="ws://unused",
            mcp_params={"count": McpToolParam(type="integer", required=True)},
        )
        probe = MagicMock(return_value=[])
        impl = MCPServerImpl(websocket_probe_executor=probe)
        impl.register_tools([conn])

        with pytest.raises(Exception) as raised:
            asyncio.run(impl.call_tool("ws_typed_feed", {"count": "bad"}))

        assert type(raised.value).__name__ == "McpArgumentValidationError"
        assert "count" in str(raised.value)
        assert "integer" in str(raised.value)
        assert "bad" not in str(raised.value)
        probe.assert_not_called()

    def test_mcp_server_impl_lists_and_dispatches_websocket_tool(self, ws_test_server) -> None:
        """MCPServerImpl registers WebSocketConnection, lists ws_* tool, and executes call_tool."""
        ws_test_server.configure(ServerBehaviorConfig(behavior=ServerBehavior.ECHO))

        conn = WebSocketConnection(
            name="Live Feed",
            expose_as_mcp=True,
            mcp_description="Live echo stream",
            url=ws_test_server.url,
            mcp_probe_max_messages=1,
            mcp_probe_max_duration_ms=3000,
        )
        http_req = RequestData(
            name="HTTP Ping",
            expose_as_mcp=True,
            method="GET",
            url="http://example.com",
        )

        impl = MCPServerImpl(websocket_probe_executor=execute_qt_websocket_probe)
        impl.register_tools([http_req, conn])

        tools = asyncio.run(impl.list_tools())
        tool_names = [t.name for t in tools]
        assert "http_ping" in tool_names
        assert "ws_live_feed" in tool_names

        # Call the WebSocket probe tool
        result = asyncio.run(impl.call_tool("ws_live_feed", {}))
        assert len(result) == 1
        assert isinstance(result[0].text, str)
        assert "=== WebSocket Probe Transcript ===" in result[0].text


# =============================================================================
# 8. Daemon Storage Snapshot Loading
# =============================================================================


class TestDaemonStorageWebSocketSupport:
    """Asserts load_collections_snapshot_strict loads Collection.websockets."""

    class MockStorage:
        def __init__(self, data_dir: Path) -> None:
            self.data_dir = data_dir
            self.collections_path = data_dir / "collections"
            self.environments_file = data_dir / "environments.json"

    def test_load_collections_snapshot_loads_websocket_profiles(self, tmp_path: Path) -> None:
        """Strict snapshot loader loads collection JSON files with websocket profiles."""
        coll_id = str(uuid.uuid4())
        coll = Collection(
            id=coll_id,
            name="Realtime Suite",
            requests=[],
            websockets=[
                WebSocketConnection(
                    name="Production Ticker",
                    expose_as_mcp=True,
                    url="wss://ticker.example.com",
                )
            ],
        )

        storage = self.MockStorage(tmp_path)
        storage.collections_path.mkdir(parents=True, exist_ok=True)
        (storage.collections_path / f"{coll_id}.json").write_text(
            coll.model_dump_json(), encoding="utf-8"
        )

        loaded = load_collections_snapshot_strict(storage, {coll_id})
        assert coll_id in loaded
        assert len(loaded[coll_id].websockets) == 1
        assert loaded[coll_id].websockets[0].name == "Production Ticker"
        assert loaded[coll_id].websockets[0].expose_as_mcp is True
