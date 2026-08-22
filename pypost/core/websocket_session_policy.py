"""Qt-free WebSocket session state machine, backoff scheduling, and policies."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import logging
import random
from typing import Optional

logger = logging.getLogger(__name__)


class SessionState(str, Enum):
    """Lifecycle states of a WebSocket session."""

    IDLE = "Idle"
    CONNECTING = "Connecting"
    OPEN = "Open"
    CLOSING = "Closing"
    CLOSED = "Closed"
    RECONNECTING = "Reconnecting"
    FAILED = "Failed"


@dataclass(frozen=True)
class StateDetail:
    """Detailed metadata describing a session state transition or error."""

    message: str = ""
    error_category: Optional[str] = None
    close_code: Optional[int] = None
    reason: Optional[str] = None


@dataclass(frozen=True)
class HeartbeatConfig:
    """Heartbeat ping/pong interval and timeout configuration."""

    interval_seconds: float = 30.0
    timeout_seconds: float = 10.0
    ping_payload: bytes = b""


@dataclass(frozen=True)
class ReconnectConfig:
    """Automatic reconnection policy configuration."""

    enabled: bool = False
    initial_delay_seconds: float = 1.0
    multiplier: float = 2.0
    max_delay_seconds: float = 60.0
    max_attempts: int = 5
    jitter: bool = True


class WebSocketSessionPolicy:
    """Pure domain logic for session transitions, backoff calculation, and reconnect rules."""

    _VALID_TRANSITIONS: dict[SessionState, set[SessionState]] = {
        SessionState.IDLE: {
            SessionState.CONNECTING,
        },
        SessionState.CONNECTING: {
            SessionState.OPEN,
            SessionState.FAILED,
            SessionState.IDLE,
        },
        SessionState.OPEN: {
            SessionState.CLOSING,
            SessionState.CLOSED,
            SessionState.RECONNECTING,
            SessionState.FAILED,
        },
        SessionState.CLOSING: {
            SessionState.CLOSED,
        },
        SessionState.RECONNECTING: {
            SessionState.OPEN,
            SessionState.RECONNECTING,
            SessionState.FAILED,
            SessionState.IDLE,
        },
        SessionState.FAILED: {
            SessionState.CONNECTING,
        },
        SessionState.CLOSED: {
            SessionState.CONNECTING,
        },
    }

    def can_transition(self, current: SessionState, target: SessionState) -> bool:
        """Evaluate whether a state transition from `current` to `target` is valid."""
        allowed = self._VALID_TRANSITIONS.get(current, set())
        valid = target in allowed
        logger.debug(
            "Evaluated state transition %s -> %s: valid=%s",
            current.value,
            target.value,
            valid,
        )
        return valid

    def calculate_backoff_delay(self, attempt: int, config: ReconnectConfig) -> float:
        """Calculate exponential backoff delay in seconds with optional jitter."""
        if attempt < 1:
            attempt = 1
        base = config.initial_delay_seconds * (config.multiplier ** (attempt - 1))
        capped = min(base, config.max_delay_seconds)
        if config.jitter:
            jittered = capped * random.uniform(0.75, 1.25)
            delay = min(jittered, config.max_delay_seconds)
        else:
            delay = capped
        logger.debug(
            "Calculated backoff delay for attempt %d: %.3fs (jitter=%s)",
            attempt,
            delay,
            config.jitter,
        )
        return delay

    def should_reconnect(
        self,
        close_code: int,
        peer_initiated: bool,
        config: ReconnectConfig,
        attempts_made: int,
    ) -> bool:
        """Determine whether an automatic reconnection should be scheduled."""
        if not config.enabled:
            logger.debug("Reconnect disabled in config")
            return False
        if attempts_made >= config.max_attempts:
            logger.debug(
                "Reconnect limit reached: attempts_made=%d max_attempts=%d",
                attempts_made,
                config.max_attempts,
            )
            return False
        # Clean closures (1000 Normal Closure, 1001 Going Away) do not reconnect
        if close_code in (1000, 1001):
            logger.debug("Clean closure code %d received; skipping reconnect", close_code)
            return False
        logger.debug(
            "Reconnection allowed: code=%d peer_initiated=%s attempt=%d/%d",
            close_code,
            peer_initiated,
            attempts_made + 1,
            config.max_attempts,
        )
        return True
