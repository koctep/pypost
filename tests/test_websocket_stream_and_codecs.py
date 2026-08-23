"""Reproduction tests for WebSocket bounded stream, codecs, export, and list model (PYPOST-1130).

Covers:
1. StreamEntry immutable dataclass and attributes.
2. build_stream_entry pure masking, truncation, wire byte_size, and lifecycle support.
3. MessageStream bounded ring buffer with dual FIFO eviction (capacity and memory budget)
   and drop counters.
4. StreamQuery filtering (direction, kind, format, text search, heartbeats toggle) and
   stream matching.
5. WebSocketCodec encoding, decoding, validation, and binary presentation detection.
6. WebSocketStreamExport JSON array and Plain Text transcript formatting, file export,
   and drop header inclusion.
7. StreamListModel (QAbstractListModel) virtualized Qt model, roles, batch append,
   eviction signaling, and stable seq identity.
8. Architectural Qt-free import isolation for core stream, codec, and export modules.
"""

from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any

import pytest

from pypost.models.websocket import WsMessageFormat
from pypost.core.websocket_transport_protocol import (
    FrameDirection,
    FrameType,
    RawFrame,
)

# Modules under test (will raise ModuleNotFoundError/ImportError until implemented in Step 4)
from pypost.core.websocket_stream import (
    MessageStream,
    StreamEntry,
    StreamQuery,
    build_stream_entry,
)
from pypost.core.websocket_codec import (
    decode_payload,
    detect_binary_presentation,
    encode_payload,
    validate_format,
)
from pypost.core.websocket_stream_export import (
    WebSocketExportError,
    export_stream_to_json_file,
    export_stream_to_text_file,
    format_json_transcript,
    format_text_transcript,
)
from pypost.ui.widgets.websocket.stream_model import StreamListModel

pytestmark = pytest.mark.timeout(30)


# ============================================================================
# Helper Factories
# ============================================================================


def _create_sample_entry(
    seq: int = 1,
    ts_utc: str = "2026-08-22T12:00:00.000Z",
    kind: str = "message",
    direction: str = "in",
    payload_format: str = "json",
    payload: str = '{"status":"ok"}',
    byte_size: int = 15,
    truncated: bool = False,
    detail: str = "",
) -> StreamEntry:
    """Helper to create a StreamEntry instance."""
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


# ============================================================================
# 1. StreamEntry Dataclass Tests
# ============================================================================


class TestStreamEntry:
    """Tests for the immutable StreamEntry dataclass."""

    @pytest.mark.timeout(30)
    def test_stream_entry_fields_and_initialization(self) -> None:
        """StreamEntry must store all required metadata and content fields."""
        entry = StreamEntry(
            seq=42,
            ts_utc="2026-08-22T11:30:00.123Z",
            kind="message",
            direction="in",
            payload_format="json",
            payload='{"key": "value"}',
            byte_size=16,
            truncated=False,
            detail="detail text",
        )
        assert entry.seq == 42
        assert entry.ts_utc == "2026-08-22T11:30:00.123Z"
        assert entry.kind == "message"
        assert entry.direction == "in"
        assert entry.payload_format == "json"
        assert entry.payload == '{"key": "value"}'
        assert entry.byte_size == 16
        assert entry.truncated is False
        assert entry.detail == "detail text"

    @pytest.mark.timeout(30)
    def test_stream_entry_is_frozen_immutable(self) -> None:
        """StreamEntry must be immutable (@dataclass(frozen=True))."""
        entry = _create_sample_entry(seq=1)
        with pytest.raises(FrozenInstanceError):
            entry.seq = 2  # type: ignore[misc]
        with pytest.raises(FrozenInstanceError):
            entry.payload = "mutated"  # type: ignore[misc]


# ============================================================================
# 2. build_stream_entry Pure Function Tests
# ============================================================================


class TestBuildStreamEntry:
    """Tests for the pure build_stream_entry factory function."""

    @pytest.mark.timeout(30)
    def test_build_stream_entry_from_raw_frame(self) -> None:
        """Converting RawFrame populates all fields with correct types and ISO UTC timestamp."""
        ts = datetime(2026, 8, 22, 11, 45, 30, 500000, tzinfo=timezone.utc)
        raw_frame = RawFrame(
            direction=FrameDirection.IN,
            payload_format=FrameType.TEXT,
            payload='{"type":"greeting","msg":"hello"}',
            byte_size=33,
            timestamp=ts,
        )
        entry = build_stream_entry(frame=raw_frame, seq=1)

        assert entry.seq == 1
        assert entry.kind == "message"
        assert entry.direction == "in"
        assert entry.payload_format == "text"
        assert entry.payload == '{"type":"greeting","msg":"hello"}'
        assert entry.byte_size == 33
        assert entry.truncated is False
        assert entry.detail == ""
        assert "2026-08-22T11:45:30.500" in entry.ts_utc

    @pytest.mark.timeout(30)
    def test_build_stream_entry_secret_masking_with_hidden_keys(self) -> None:
        """Secret values referenced by hidden_keys in env_vars must be redacted with '***'."""
        env_vars = {
            "API_SECRET": "SuperSecretToken12345",
            "PUBLIC_VAR": "PublicValue",
        }
        hidden_keys = ["API_SECRET"]

        raw_frame = RawFrame(
            direction=FrameDirection.OUT,
            payload_format=FrameType.TEXT,
            payload='{"auth": "Bearer SuperSecretToken12345", "name": "PublicValue"}',
            byte_size=63,
            timestamp=datetime.now(timezone.utc),
        )

        entry = build_stream_entry(
            frame=raw_frame,
            seq=2,
            env_vars=env_vars,
            hidden_keys=hidden_keys,
        )

        assert "SuperSecretToken12345" not in entry.payload
        assert "***" in entry.payload
        assert "PublicValue" in entry.payload

    @pytest.mark.timeout(30)
    def test_build_stream_entry_display_truncation_preserves_wire_byte_size(self) -> None:
        """Payload exceeding truncate_bytes is truncated in payload but retains full byte_size."""
        large_text = "A" * 1000  # 1000 bytes
        raw_frame = RawFrame(
            direction=FrameDirection.IN,
            payload_format=FrameType.TEXT,
            payload=large_text,
            byte_size=1000,
            timestamp=datetime.now(timezone.utc),
        )

        entry = build_stream_entry(
            frame=raw_frame,
            seq=3,
            truncate_bytes=256,
        )

        assert len(entry.payload) == 256
        assert entry.byte_size == 1000
        assert entry.truncated is True

    @pytest.mark.timeout(30)
    def test_build_stream_entry_no_truncation_when_within_limit(self) -> None:
        """Payload within truncate_bytes is not truncated."""
        payload = "Short payload"
        raw_frame = RawFrame(
            direction=FrameDirection.OUT,
            payload_format=FrameType.TEXT,
            payload=payload,
            byte_size=len(payload.encode("utf-8")),
            timestamp=datetime.now(timezone.utc),
        )

        entry = build_stream_entry(
            frame=raw_frame,
            seq=4,
            truncate_bytes=256,
        )

        assert entry.payload == payload
        assert entry.byte_size == len(payload.encode("utf-8"))
        assert entry.truncated is False

    @pytest.mark.timeout(30)
    def test_build_stream_entry_lifecycle_event_construction(self) -> None:
        """Lifecycle events (connected, heartbeat) can be constructed without a RawFrame."""
        entry = build_stream_entry(
            seq=5,
            kind="lifecycle",
            direction="none",
            payload="",
            byte_size=0,
            detail="Connected subprotocol=json.v2",
        )

        assert entry.seq == 5
        assert entry.kind == "lifecycle"
        assert entry.direction == "none"
        assert entry.payload == ""
        assert entry.byte_size == 0
        assert entry.detail == "Connected subprotocol=json.v2"
        assert entry.truncated is False


# ============================================================================
# 3. MessageStream Bounded Ring Buffer & Dual Eviction Tests
# ============================================================================


class TestMessageStream:
    """Tests for bounded MessageStream ring buffer and dual eviction."""

    @pytest.mark.timeout(30)
    def test_message_stream_initial_state(self) -> None:
        """Newly created MessageStream must be empty with zero drop counts."""
        stream = MessageStream(max_entries=100, memory_budget_bytes=1024)
        assert len(stream) == 0
        assert stream.total_retained_bytes == 0
        assert stream.dropped == {"capacity": 0, "memory_budget": 0}
        assert stream.snapshot() == ()

    @pytest.mark.timeout(30)
    def test_message_stream_append_and_indexing(self) -> None:
        """Appended entries are stored in chronological order and accessible by index."""
        stream = MessageStream(max_entries=10, memory_budget_bytes=10000)
        e1 = _create_sample_entry(seq=1, payload="entry 1")
        e2 = _create_sample_entry(seq=2, payload="entry 2")

        evicted1, reason1 = stream.append(e1)
        assert evicted1 == 0
        assert reason1 is None

        evicted2, reason2 = stream.append(e2)
        assert evicted2 == 0
        assert reason2 is None

        assert len(stream) == 2
        assert stream[0] == e1
        assert stream[1] == e2
        assert stream.snapshot() == (e1, e2)

    @pytest.mark.timeout(30)
    def test_message_stream_capacity_eviction_oldest_first(self) -> None:
        """Exceeding max_entries evicts oldest entries and increments dropped['capacity']."""
        stream = MessageStream(max_entries=3, memory_budget_bytes=100_000)
        entries = [_create_sample_entry(seq=i, payload=f"payload {i}") for i in range(1, 6)]

        for entry in entries[:3]:
            evicted, reason = stream.append(entry)
            assert evicted == 0
            assert reason is None

        assert len(stream) == 3
        assert stream.dropped["capacity"] == 0

        # Append 4th entry -> evicts entry seq=1
        evicted, reason = stream.append(entries[3])
        assert evicted == 1
        assert reason == "capacity"
        assert len(stream) == 3
        assert stream[0].seq == 2
        assert stream[1].seq == 3
        assert stream[2].seq == 4
        assert stream.dropped["capacity"] == 1
        assert stream.dropped["memory_budget"] == 0

        # Append 5th entry -> evicts entry seq=2
        evicted, reason = stream.append(entries[4])
        assert evicted == 1
        assert reason == "capacity"
        assert len(stream) == 3
        assert stream[0].seq == 3
        assert stream[1].seq == 4
        assert stream[2].seq == 5
        assert stream.dropped["capacity"] == 2

    @pytest.mark.timeout(30)
    def test_message_stream_memory_budget_eviction(self) -> None:
        """Exceeding memory_budget_bytes evicts oldest entries and increments dropped budget."""
        # Budget: 100 bytes
        stream = MessageStream(max_entries=100, memory_budget_bytes=100)

        # Append 3 entries of 40 bytes each
        e1 = _create_sample_entry(seq=1, payload="x" * 40)
        e2 = _create_sample_entry(seq=2, payload="y" * 40)
        e3 = _create_sample_entry(seq=3, payload="z" * 40)

        stream.append(e1)  # retained: 40 bytes
        stream.append(e2)  # retained: 80 bytes
        assert len(stream) == 2
        assert stream.dropped["memory_budget"] == 0

        # Adding e3 (40B) makes total 120 > 100 bytes -> evicts e1 (40B), leaving e2 and e3 (80B)
        evicted, reason = stream.append(e3)
        assert evicted == 1
        assert reason == "memory_budget"
        assert len(stream) == 2
        assert stream[0].seq == 2
        assert stream[1].seq == 3
        assert stream.total_retained_bytes == 80
        assert stream.dropped["memory_budget"] == 1
        assert stream.dropped["capacity"] == 0

    @pytest.mark.timeout(30)
    def test_message_stream_budget_eviction_multiple_entries_for_large_payload(self) -> None:
        """Appending an entry larger than existing entries evicts multiple older entries."""
        stream = MessageStream(max_entries=100, memory_budget_bytes=100)

        for i in range(1, 6):
            stream.append(_create_sample_entry(seq=i, payload="a" * 15))  # 5 * 15 = 75 bytes

        assert len(stream) == 5
        assert stream.total_retained_bytes == 75

        # Append large entry of 70 bytes -> 75 + 70 = 145 > 100
        # Evicts seq 1 (15B), 2 (15B), 3 (15B) -> 75 - 45 + 70 = 100 bytes
        large_entry = _create_sample_entry(seq=6, payload="b" * 70)
        evicted, reason = stream.append(large_entry)

        assert evicted == 3
        assert reason == "memory_budget"
        assert len(stream) == 3
        assert [e.seq for e in stream.snapshot()] == [4, 5, 6]
        assert stream.dropped["memory_budget"] == 3
        assert stream.total_retained_bytes == 100

    @pytest.mark.timeout(30)
    def test_message_stream_snapshot_immutability(self) -> None:
        """Mutating stream after calling snapshot() must not mutate the returned tuple."""
        stream = MessageStream(max_entries=5, memory_budget_bytes=1000)
        e1 = _create_sample_entry(seq=1, payload="initial")
        stream.append(e1)

        snap = stream.snapshot()
        assert len(snap) == 1

        e2 = _create_sample_entry(seq=2, payload="second")
        stream.append(e2)

        assert len(snap) == 1
        assert len(stream.snapshot()) == 2

    @pytest.mark.timeout(30)
    def test_message_stream_clear_resets_all_state(self) -> None:
        """clear() must empty the buffer and reset retained bytes and drop counters to zero."""
        stream = MessageStream(max_entries=2, memory_budget_bytes=50)
        stream.append(_create_sample_entry(seq=1, payload="data 1"))
        stream.append(_create_sample_entry(seq=2, payload="data 2"))
        stream.append(_create_sample_entry(seq=3, payload="data 3"))  # forces capacity drop

        assert len(stream) == 2
        assert stream.dropped["capacity"] == 1

        stream.clear()

        assert len(stream) == 0
        assert stream.total_retained_bytes == 0
        assert stream.dropped == {"capacity": 0, "memory_budget": 0}
        assert stream.snapshot() == ()


# ============================================================================
# 4. StreamQuery Filtering & Stream Matching Tests
# ============================================================================


class TestStreamQuery:
    """Tests for StreamQuery predicate and MessageStream.matching filter evaluation."""

    @pytest.mark.timeout(30)
    def test_stream_query_filter_by_direction(self) -> None:
        """StreamQuery filtering by direction ('in', 'out')."""
        q_in = StreamQuery(direction="in")
        q_out = StreamQuery(direction="out")

        e_in = _create_sample_entry(seq=1, direction="in")
        e_out = _create_sample_entry(seq=2, direction="out")

        assert q_in.matches(e_in) is True
        assert q_in.matches(e_out) is False
        assert q_out.matches(e_in) is False
        assert q_out.matches(e_out) is True

    @pytest.mark.timeout(30)
    def test_stream_query_filter_by_kind(self) -> None:
        """StreamQuery filtering by kind ('message', 'lifecycle')."""
        q_msg = StreamQuery(kind="message")
        q_life = StreamQuery(kind="lifecycle")

        e_msg = _create_sample_entry(seq=1, kind="message")
        e_life = _create_sample_entry(seq=2, kind="lifecycle", detail="connected")

        assert q_msg.matches(e_msg) is True
        assert q_msg.matches(e_life) is False
        assert q_life.matches(e_msg) is False
        assert q_life.matches(e_life) is True

    @pytest.mark.timeout(30)
    def test_stream_query_filter_by_payload_format(self) -> None:
        """StreamQuery filtering by payload format ('json', 'hex', 'base64', 'text')."""
        q_json = StreamQuery(payload_format="json")
        q_hex = StreamQuery(payload_format="hex")

        e_json = _create_sample_entry(seq=1, payload_format="json")
        e_hex = _create_sample_entry(seq=2, payload_format="hex")

        assert q_json.matches(e_json) is True
        assert q_json.matches(e_hex) is False
        assert q_hex.matches(e_hex) is True

    @pytest.mark.timeout(30)
    def test_stream_query_search_text_case_insensitive(self) -> None:
        """search_text matches case-insensitively in payload or detail."""
        query = StreamQuery(search_text="telemetry")

        e_match_payload = _create_sample_entry(seq=1, payload='{"topic": "Telemetry/GPS"}')
        e_match_detail = _create_sample_entry(
            seq=2, payload="", detail="Telemetry subscription established"
        )
        e_no_match = _create_sample_entry(seq=3, payload='{"status": "ok"}', detail="")

        assert query.matches(e_match_payload) is True
        assert query.matches(e_match_detail) is True
        assert query.matches(e_no_match) is False

    @pytest.mark.timeout(30)
    def test_stream_query_heartbeats_toggle(self) -> None:
        """show_heartbeats=False excludes ping/pong lifecycle events."""
        q_no_hb = StreamQuery(show_heartbeats=False)
        q_with_hb = StreamQuery(show_heartbeats=True)

        e_ping = _create_sample_entry(seq=1, kind="lifecycle", detail="Ping sent")
        e_pong = _create_sample_entry(seq=2, kind="lifecycle", detail="Pong received (12ms)")
        e_connected = _create_sample_entry(
            seq=3, kind="lifecycle", detail="Connected to ws://example.com"
        )
        e_msg = _create_sample_entry(seq=4, kind="message", payload="hello")

        # When show_heartbeats is False, ping/pong are suppressed, other lifecycles/messages pass
        assert q_no_hb.matches(e_ping) is False
        assert q_no_hb.matches(e_pong) is False
        assert q_no_hb.matches(e_connected) is True
        assert q_no_hb.matches(e_msg) is True

        # When show_heartbeats is True, all pass
        assert q_with_hb.matches(e_ping) is True
        assert q_with_hb.matches(e_pong) is True

    @pytest.mark.timeout(30)
    def test_message_stream_matching_returns_sequence_numbers(self) -> None:
        """MessageStream.matching(query) returns a sequence of matching entry seq IDs."""
        stream = MessageStream(max_entries=10)
        e1 = _create_sample_entry(seq=101, direction="in", payload='{"op": "subscribe"}')
        e2 = _create_sample_entry(seq=102, direction="out", payload='{"op": "publish"}')
        e3 = _create_sample_entry(seq=103, direction="in", payload='{"op": "ping"}')

        stream.append(e1)
        stream.append(e2)
        stream.append(e3)

        q = StreamQuery(direction="in")
        matching_seqs = stream.matching(q)

        assert tuple(matching_seqs) == (101, 103)


# ============================================================================
# 5. WebSocketCodec Multi-Format Codec Tests
# ============================================================================


class TestWebSocketCodec:
    """Tests for multi-format encoding, decoding, validation, and binary presentation."""

    @pytest.mark.timeout(30)
    def test_codec_text_roundtrip(self) -> None:
        """Text format round-trip encoding and decoding."""
        raw_text = "Hello, WebSocket! 🚀"
        encoded = encode_payload(raw_text, WsMessageFormat.TEXT)
        decoded = decode_payload(encoded, WsMessageFormat.TEXT)
        assert decoded == raw_text

    @pytest.mark.timeout(30)
    def test_codec_json_roundtrip_and_validation(self) -> None:
        """JSON format validates syntax and decodes to structured text."""
        valid_json = '{"command": "subscribe", "channel": "sensor_1"}'
        encoded = encode_payload(valid_json, WsMessageFormat.JSON)
        decoded = decode_payload(encoded, WsMessageFormat.JSON)

        # Parsed structure must match
        assert json.loads(decoded) == json.loads(valid_json)

    @pytest.mark.timeout(30)
    def test_codec_json_encode_invalid_syntax_raises_value_error(self) -> None:
        """Encoding invalid JSON text must raise ValueError."""
        invalid_json = '{"unclosed": "brace"'
        with pytest.raises(ValueError, match="(?i)json"):
            encode_payload(invalid_json, WsMessageFormat.JSON)

    @pytest.mark.timeout(30)
    def test_codec_hex_roundtrip(self) -> None:
        """Hexadecimal format round-trip: hex string <-> bytes."""
        hex_str = "0102030405060708090a0b0c0d0e0f"
        encoded = encode_payload(hex_str, WsMessageFormat.HEX)
        assert isinstance(encoded, bytes)
        assert encoded == bytes.fromhex(hex_str)

        decoded = decode_payload(encoded, WsMessageFormat.HEX)
        assert decoded.lower() == hex_str.lower()

    @pytest.mark.timeout(30)
    def test_codec_hex_invalid_syntax_raises_value_error(self) -> None:
        """Invalid hexadecimal string (odd length or non-hex chars) raises ValueError."""
        with pytest.raises(ValueError, match="(?i)hex"):
            encode_payload("01020", WsMessageFormat.HEX)  # odd length

        with pytest.raises(ValueError, match="(?i)hex"):
            encode_payload("0102ZZ", WsMessageFormat.HEX)  # invalid characters

    @pytest.mark.timeout(30)
    def test_codec_base64_roundtrip(self) -> None:
        """Base64 format round-trip: Base64 string <-> bytes."""
        b64_str = "AQIDBAUGBwgJCgsMDQ4P"
        encoded = encode_payload(b64_str, WsMessageFormat.BASE64)
        assert isinstance(encoded, bytes)

        decoded = decode_payload(encoded, WsMessageFormat.BASE64)
        assert decoded == b64_str

    @pytest.mark.timeout(30)
    def test_codec_base64_invalid_syntax_raises_value_error(self) -> None:
        """Corrupted Base64 string raises ValueError."""
        with pytest.raises(ValueError, match="(?i)base64"):
            encode_payload("Invalid Base64 @@@!!!", WsMessageFormat.BASE64)

    @pytest.mark.timeout(30)
    def test_detect_binary_presentation_defaults_to_hex(self) -> None:
        """detect_binary_presentation must default to WsMessageFormat.HEX."""
        binary_data = b"\x00\x01\x02\xfe\xff"
        presentation = detect_binary_presentation(binary_data)
        assert presentation == WsMessageFormat.HEX

    @pytest.mark.timeout(30)
    def test_validate_format(self) -> None:
        """validate_format returns (True, None) for valid data and (False, err_msg) for invalid."""
        # Text always valid
        assert validate_format("any text", WsMessageFormat.TEXT) == (True, None)

        # JSON
        assert validate_format('{"valid": true}', WsMessageFormat.JSON) == (True, None)
        valid_json_err, err_json = validate_format("{invalid", WsMessageFormat.JSON)
        assert valid_json_err is False
        assert err_json is not None

        # Hex
        assert validate_format("deadbeef", WsMessageFormat.HEX) == (True, None)
        valid_hex_err, err_hex = validate_format("deadbeefZ", WsMessageFormat.HEX)
        assert valid_hex_err is False
        assert err_hex is not None

        # Base64
        assert validate_format("3q2+7w==", WsMessageFormat.BASE64) == (True, None)
        valid_b64_err, err_b64 = validate_format("Invalid Base64 ===", WsMessageFormat.BASE64)
        assert valid_b64_err is False
        assert err_b64 is not None


# ============================================================================
# 6. WebSocketStreamExport Transcript Export Tests
# ============================================================================


class TestWebSocketStreamExport:
    """Tests for JSON array and Plain Text transcript exports with drop metadata."""

    @pytest.mark.timeout(30)
    def test_format_json_transcript_structure_and_metadata(self) -> None:
        """format_json_transcript produces schema_version, metadata, and entry array."""
        stream = MessageStream(max_entries=2)
        stream.append(_create_sample_entry(seq=1, payload="entry 1"))
        stream.append(_create_sample_entry(seq=2, payload="entry 2"))
        stream.append(_create_sample_entry(seq=3, payload="entry 3"))  # evicted seq 1

        transcript = format_json_transcript(stream, metadata={"session_id": "ws-123"})

        assert transcript["schema_version"] == "1.0"
        assert transcript["metadata"]["total_retained"] == 2
        assert transcript["metadata"]["dropped"] == {"capacity": 1, "memory_budget": 0}
        assert transcript["metadata"]["session_id"] == "ws-123"
        assert len(transcript["entries"]) == 2
        assert transcript["entries"][0]["seq"] == 2
        assert transcript["entries"][1]["seq"] == 3

    @pytest.mark.timeout(30)
    def test_format_text_transcript_header_and_lines(self) -> None:
        """format_text_transcript produces human-readable header and formatted log lines."""
        stream = MessageStream(max_entries=5)
        stream.append(
            _create_sample_entry(
                seq=1,
                ts_utc="2026-08-22T11:00:00.000Z",
                direction="in",
                byte_size=15,
                payload='{"status":"ok"}',
            )
        )
        stream.append(
            _create_sample_entry(
                seq=2,
                ts_utc="2026-08-22T11:00:01.000Z",
                direction="out",
                byte_size=2000,
                truncated=True,
                payload="truncated data...",
            )
        )
        stream.append(
            _create_sample_entry(
                seq=3,
                ts_utc="2026-08-22T11:00:02.000Z",
                kind="lifecycle",
                direction="none",
                byte_size=0,
                detail="Disconnected (code 1000)",
            )
        )

        text = format_text_transcript(stream)

        # Header assertions
        assert "# PyPost WebSocket Transcript" in text
        assert "# Retained entries: 3" in text
        assert "# Dropped entries: capacity=0, memory_budget=0" in text

        # Line assertions
        assert '[2026-08-22T11:00:00.000Z] [in] [15B] {"status": "ok"}' in text
        assert "[2026-08-22T11:00:01.000Z] [out] [2000B] [TRUNCATED] truncated data..." in text
        assert "[2026-08-22T11:00:02.000Z] [none] [0B] [lifecycle] Disconnected (code 1000)" in text

    @pytest.mark.timeout(30)
    def test_export_stream_to_json_file_writes_and_reproduces_identically(
        self, tmp_path: Path
    ) -> None:
        """export_stream_to_json_file writes valid JSON reproducibly."""
        stream = MessageStream(max_entries=10)
        stream.append(_create_sample_entry(seq=1, payload="test 1"))
        stream.append(_create_sample_entry(seq=2, payload="test 2"))

        out_file1 = tmp_path / "subdir" / "transcript1.json"
        out_file2 = tmp_path / "subdir" / "transcript2.json"

        metadata = {"exported_at": "2026-08-22T12:00:00.000Z"}
        export_stream_to_json_file(out_file1, stream, metadata=metadata)
        export_stream_to_json_file(out_file2, stream, metadata=metadata)

        assert out_file1.exists()
        assert out_file2.exists()
        assert out_file1.read_bytes() == out_file2.read_bytes()

        parsed = json.loads(out_file1.read_text(encoding="utf-8"))
        assert parsed["schema_version"] == "1.0"
        assert len(parsed["entries"]) == 2

    @pytest.mark.timeout(30)
    def test_export_stream_to_text_file_writes_to_disk(self, tmp_path: Path) -> None:
        """export_stream_to_text_file writes UTF-8 text transcript to path."""
        stream = MessageStream(max_entries=10)
        stream.append(_create_sample_entry(seq=1, payload="line 1"))

        out_file = tmp_path / "logs" / "transcript.txt"
        export_stream_to_text_file(out_file, stream)

        assert out_file.exists()
        content = out_file.read_text(encoding="utf-8")
        assert "# PyPost WebSocket Transcript" in content
        assert "line 1" in content

    @pytest.mark.timeout(30)
    def test_export_stream_wraps_write_errors_in_websocket_export_error(
        self, tmp_path: Path
    ) -> None:
        """Write errors must be wrapped in WebSocketExportError."""
        stream = MessageStream(max_entries=10)
        # Attempt to write to a path where parent is a file rather than directory
        parent_file = tmp_path / "not_a_dir"
        parent_file.write_text("blocking file", encoding="utf-8")
        invalid_path = parent_file / "export.json"

        with pytest.raises(WebSocketExportError):
            export_stream_to_json_file(invalid_path, stream)


# ============================================================================
# 7. StreamListModel (PySide6 QAbstractListModel) Virtualized Model Tests
# ============================================================================


class TestStreamListModel:
    """Tests for the Qt virtualized StreamListModel over MessageStream."""

    @pytest.mark.timeout(30)
    def test_stream_list_model_roles_and_row_count(self, qapp: Any) -> None:
        """StreamListModel exposes rowCount and custom role data for items."""
        from PySide6.QtCore import QModelIndex, Qt

        stream = MessageStream(max_entries=10)
        e1 = _create_sample_entry(
            seq=1,
            ts_utc="2026-08-22T11:00:00.000Z",
            kind="message",
            direction="in",
            payload_format="json",
            payload='{"a": 1}',
            byte_size=8,
            truncated=False,
            detail="ok",
        )
        stream.append(e1)

        model = StreamListModel(stream=stream)
        assert model.rowCount(QModelIndex()) == 1

        idx = model.index(0, 0, QModelIndex())
        assert model.data(idx, Qt.ItemDataRole.DisplayRole) == '{"a": 1}'
        assert model.data(idx, StreamListModel.SeqRole) == 1
        assert model.data(idx, StreamListModel.TimestampRole) == "2026-08-22T11:00:00.000Z"
        assert model.data(idx, StreamListModel.KindRole) == "message"
        assert model.data(idx, StreamListModel.DirectionRole) == "in"
        assert model.data(idx, StreamListModel.FormatRole) == "json"
        assert model.data(idx, StreamListModel.TruncatedRole) is False
        assert model.data(idx, StreamListModel.ByteSizeRole) == 8
        assert model.data(idx, StreamListModel.DetailRole) == "ok"
        assert model.data(idx, StreamListModel.StreamEntryRole) == e1

    @pytest.mark.timeout(30)
    def test_stream_list_model_append_batch_and_signals(self, qapp: Any) -> None:
        """append_batch inserts entries and emits rowsInserted Qt signals."""
        from PySide6.QtCore import QModelIndex

        model = StreamListModel()
        inserted_signals: list[tuple[int, int]] = []
        model.rowsInserted.connect(
            lambda parent, first, last: inserted_signals.append((first, last))
        )

        e1 = _create_sample_entry(seq=1, payload="msg 1")
        e2 = _create_sample_entry(seq=2, payload="msg 2")

        inserted, evicted = model.append_batch([e1, e2])

        assert inserted == 2
        assert evicted == 0
        assert model.rowCount(QModelIndex()) == 2
        assert inserted_signals == [(0, 1)]

    @pytest.mark.timeout(30)
    def test_stream_list_model_append_batch_eviction_signals_and_stable_seq(
        self, qapp: Any
    ) -> None:
        """append_batch emits removal/insertion signals on eviction and preserves stable seq."""
        from PySide6.QtCore import QModelIndex

        stream = MessageStream(max_entries=3)
        model = StreamListModel(stream=stream)

        # Fill capacity (3 entries)
        model.append_batch([_create_sample_entry(seq=i, payload=f"msg {i}") for i in range(1, 4)])
        assert model.rowCount(QModelIndex()) == 3

        removed_signals: list[tuple[int, int]] = []
        inserted_signals: list[tuple[int, int]] = []
        model.rowsRemoved.connect(
            lambda parent, first, last: removed_signals.append((first, last))
        )
        model.rowsInserted.connect(
            lambda parent, first, last: inserted_signals.append((first, last))
        )

        # Append 2 new entries (seq 4, 5) -> forces eviction of 2 oldest (seq 1, 2)
        e4 = _create_sample_entry(seq=4, payload="msg 4")
        e5 = _create_sample_entry(seq=5, payload="msg 5")

        inserted, evicted = model.append_batch([e4, e5])

        assert inserted == 2
        assert evicted == 2
        assert model.rowCount(QModelIndex()) == 3

        # Model should contain seq 3, 4, 5
        idx0 = model.index(0, 0, QModelIndex())
        idx1 = model.index(1, 0, QModelIndex())
        idx2 = model.index(2, 0, QModelIndex())

        assert model.data(idx0, StreamListModel.SeqRole) == 3
        assert model.data(idx1, StreamListModel.SeqRole) == 4
        assert model.data(idx2, StreamListModel.SeqRole) == 5

        assert len(removed_signals) >= 1
        assert len(inserted_signals) >= 1

    @pytest.mark.timeout(30)
    def test_stream_list_model_clear_resets_model(self, qapp: Any) -> None:
        """clear() emits modelReset signals and empties the model."""
        from PySide6.QtCore import QModelIndex

        model = StreamListModel()
        model.append_batch([_create_sample_entry(seq=1), _create_sample_entry(seq=2)])
        assert model.rowCount(QModelIndex()) == 2

        reset_called = []
        model.modelReset.connect(lambda: reset_called.append(True))

        model.clear()

        assert model.rowCount(QModelIndex()) == 0
        assert reset_called == [True]
        assert len(model.stream) == 0


# ============================================================================
# 8. Strict Architectural Layering Tests (Qt-Free Isolation)
# ============================================================================


class TestArchitecturalLayering:
    """Verify that core stream, codec, and export modules have zero Qt / PySide6 imports."""

    @pytest.mark.timeout(30)
    def test_core_websocket_stream_is_qt_free(self) -> None:
        """pypost/core/websocket_stream.py must not import Qt or PySide6."""
        core_file = Path(__file__).resolve().parents[1] / "pypost" / "core" / "websocket_stream.py"
        assert core_file.exists(), f"Expected {core_file} to exist"
        tree = ast.parse(core_file.read_text(encoding="utf-8"), filename=str(core_file))
        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)

        qt_imports = [imp for imp in imports if "PySide6" in imp or "Qt" in imp or "QtCore" in imp]
        assert not qt_imports, (
            f"pypost/core/websocket_stream.py contains forbidden Qt imports: {qt_imports}"
        )

    @pytest.mark.timeout(30)
    def test_core_websocket_codec_is_qt_free(self) -> None:
        """pypost/core/websocket_codec.py must not import Qt or PySide6."""
        core_file = Path(__file__).resolve().parents[1] / "pypost" / "core" / "websocket_codec.py"
        assert core_file.exists(), f"Expected {core_file} to exist"
        tree = ast.parse(core_file.read_text(encoding="utf-8"), filename=str(core_file))
        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)

        qt_imports = [imp for imp in imports if "PySide6" in imp or "Qt" in imp or "QtCore" in imp]
        assert not qt_imports, (
            f"pypost/core/websocket_codec.py contains forbidden Qt imports: {qt_imports}"
        )

    @pytest.mark.timeout(30)
    def test_core_websocket_stream_export_is_qt_free(self) -> None:
        """pypost/core/websocket_stream_export.py must not import Qt or PySide6."""
        export_file = (
            Path(__file__).resolve().parents[1] / "pypost" / "core" / "websocket_stream_export.py"
        )
        assert export_file.exists(), f"Expected {export_file} to exist"
        tree = ast.parse(export_file.read_text(encoding="utf-8"), filename=str(export_file))
        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)

        qt_imports = [imp for imp in imports if "PySide6" in imp or "Qt" in imp or "QtCore" in imp]
        assert not qt_imports, (
            f"pypost/core/websocket_stream_export.py contains forbidden Qt imports: {qt_imports}"
        )


# ============================================================================
# 9. Observability and Structured Logging Tests
# ============================================================================


class TestObservability:
    """Verify structured logging events and metric accounting."""

    @pytest.mark.timeout(30)
    def test_message_stream_eviction_and_clear_logging(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """MessageStream logs debug events on eviction and clear."""
        stream = MessageStream(max_entries=2)
        with caplog.at_level(logging.DEBUG):
            stream.append(_create_sample_entry(seq=1, payload="m1"))
            stream.append(_create_sample_entry(seq=2, payload="m2"))
            stream.append(_create_sample_entry(seq=3, payload="m3"))
            stream.clear()

        records = [r.getMessage() for r in caplog.records]
        assert any(
            "websocket_stream_eviction_triggered cause=capacity evicted_count=1" in msg
            for msg in records
        )
        assert any("websocket_stream_cleared" in msg for msg in records)

    @pytest.mark.timeout(30)
    def test_websocket_stream_export_logging(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """websocket_stream_export logs info events on JSON and Text export completion."""
        stream = MessageStream(max_entries=10)
        stream.append(_create_sample_entry(seq=1, payload="test line"))

        json_path = tmp_path / "export.json"
        text_path = tmp_path / "export.txt"

        with caplog.at_level(logging.INFO):
            export_stream_to_json_file(json_path, stream)
            export_stream_to_text_file(text_path, stream)

        records = [r.getMessage() for r in caplog.records]
        assert any(
            "websocket_stream_json_exported" in msg and "entries_count=1" in msg
            for msg in records
        )
        assert any(
            "websocket_stream_text_exported" in msg and "entries_count=1" in msg
            for msg in records
        )

    @pytest.mark.timeout(30)
    def test_stream_list_model_logging(
        self, qapp: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """StreamListModel logs debug events on batch append, eviction signal, and clear."""
        stream = MessageStream(max_entries=2)
        model = StreamListModel(stream=stream)

        with caplog.at_level(logging.DEBUG):
            model.append_batch([_create_sample_entry(seq=1), _create_sample_entry(seq=2)])
            model.append_batch([_create_sample_entry(seq=3)])
            model.clear()

        records = [r.getMessage() for r in caplog.records]
        assert any("websocket_stream_model_batch_appended inserted=2" in msg for msg in records)
        assert any("websocket_stream_model_eviction_signaled evicted=1" in msg for msg in records)
        assert any("websocket_stream_model_cleared" in msg for msg in records)
