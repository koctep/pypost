"""Qt-free probe configuration, stopping conditions, and transcript formatter.

PYPOST-1137 / WS-9 — Bounded MCP WebSocket probe domain layer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Mapping, Optional, Set

from pypost.core.mcp_response_sanitizer import McpResponseSanitizer
from pypost.core.websocket_transport_protocol import HandshakeTarget
from pypost.models.settings import AppSettings
from pypost.models.websocket import WebSocketConnection


class ProbeOutcome(str, Enum):
    """All possible outcomes for a bounded WebSocket probe execution."""

    SUCCESS = "success"
    LIMIT_REACHED = "limit_reached"
    STOP_WHEN_MATCHED = "stop_when_matched"
    TIMEOUT = "timeout"
    ERROR = "error"
    REFUSED = "refused"


@dataclass(frozen=True)
class ProbeEvent:
    """One recorded event in the probe transcript (connect/sent/received/closed/error)."""

    timestamp_iso: str
    direction: str  # "connect" | "sent" | "received" | "closed" | "error" | "timeout"
    payload: str
    is_binary: bool = False
    byte_size: int = 0


@dataclass(frozen=True)
class WebSocketProbeConfig:
    """Resolved, immutable configuration for one bounded WebSocket probe run."""

    target: HandshakeTarget
    initial_payload: Optional[str] = None
    initial_format: str = "json"
    max_messages: int = 10
    max_duration_ms: int = 10_000
    stop_when: Optional[str] = None
    probe_id: str = ""


@dataclass
class WebSocketProbeResult:
    """Collected outcome and event log produced by one bounded probe execution."""

    outcome: ProbeOutcome
    messages_received: int
    duration_ms: float
    events: List[ProbeEvent] = field(default_factory=list)
    close_code: Optional[int] = None
    close_reason: Optional[str] = None
    error_message: Optional[str] = None


def calculate_effective_probe_limits(
    conn: WebSocketConnection,
    settings: Optional[AppSettings] = None,
) -> tuple[int, int]:
    """Return (max_messages, max_duration_ms) clamped to global operator ceilings.

    Per-profile overrides can lower limits below the global default but cannot
    exceed the global ceiling configured in ``AppSettings``.

    Args:
        conn: WebSocket connection profile with optional per-profile overrides.
        settings: Application settings carrying global ceiling values.

    Returns:
        Tuple of (effective_max_messages, effective_max_duration_ms).
    """
    global_max_msgs = settings.ws_mcp_probe_max_messages if settings else 10
    global_max_dur = settings.ws_mcp_probe_max_duration_ms if settings else 10_000

    profile_msgs = conn.mcp_probe_max_messages or global_max_msgs
    profile_dur = conn.mcp_probe_max_duration_ms or global_max_dur

    effective_msgs = max(1, min(profile_msgs, global_max_msgs))
    effective_dur = max(100, min(profile_dur, global_max_dur))
    return effective_msgs, effective_dur


class WebSocketProbeStopCondition:
    """Stateful evaluator for probe stopping conditions.

    Tracks message count and evaluates the ``stop_when`` substring match.
    Duration-based stopping is handled by the hard-deadline ``QTimer`` in the runner.
    """

    def __init__(self, max_messages: int, stop_when: Optional[str] = None) -> None:
        self.max_messages = max_messages
        self.stop_when = stop_when
        self.messages_count = 0

    def should_stop(self, message: str) -> tuple[bool, Optional[ProbeOutcome]]:
        """Evaluate whether probe intake should stop after receiving ``message``.

        Args:
            message: The received text frame payload.

        Returns:
            Tuple of (should_stop, outcome_if_stopping).
            If should_stop is False, outcome is None.
        """
        self.messages_count += 1
        if self.stop_when and self.stop_when in message:
            return True, ProbeOutcome.STOP_WHEN_MATCHED
        if self.messages_count >= self.max_messages:
            return True, ProbeOutcome.LIMIT_REACHED
        return False, None


def format_probe_transcript(
    result: WebSocketProbeResult,
    *,
    env_vars: Mapping[str, str],
    hidden_keys: Set[str],
) -> str:
    """Format a probe result into a structured, sanitized transcript string.

    Masking policy applied before returning:
    - All environment variable VALUES are redacted (env vars resolved into URLs/headers).
    - Any literal strings listed in ``hidden_keys`` are redacted (exact substring match).
    - Heuristic bearer/query-token patterns applied by ``sanitize_text``.

    Args:
        result: The completed probe result from ``WebSocketProbeRunner``.
        env_vars: Active environment variable snapshot; all values are masked.
        hidden_keys: Literal strings to redact from the transcript text.

    Returns:
        A human-readable, sanitized multi-line transcript string.
    """
    lines: list[str] = [
        "=== WebSocket Probe Transcript ===",
        f"Outcome: {result.outcome.value}",
        f"Duration: {result.duration_ms:.1f}ms",
        f"Messages Received: {result.messages_received}",
    ]
    if result.close_code is not None:
        lines.append(
            f"Close Code: {result.close_code} ({result.close_reason or 'No reason'})"
        )
    if result.error_message:
        lines.append(f"Error: {result.error_message}")
    lines.append("--- Event Log ---")
    for event in result.events:
        lines.append(
            f"[{event.timestamp_iso}] [{event.direction.upper()}] {event.payload}"
        )
    raw_transcript = "\n".join(lines)

    # Pass all env_var keys as hidden_keys so their values are masked, plus
    # treat hidden_keys themselves as literal secret strings to redact.
    all_hidden = set(env_vars.keys()) | hidden_keys

    # Build a synthetic env_vars map that includes the literal hidden_key strings
    # as both key and value so _redact_hidden_values catches them.
    augmented_env: dict[str, str] = dict(env_vars)
    for literal in hidden_keys:
        if literal and literal not in augmented_env:
            augmented_env[literal] = literal

    return McpResponseSanitizer.sanitize_text(
        raw_transcript,
        env_vars=augmented_env,
        hidden_keys=all_hidden,
    )
