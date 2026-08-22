"""WebSocket message stream data models, ring buffer, and pure factories (PYPOST-1130).

Provides bounded message retention with dual FIFO eviction (capacity count
and byte-budget limit), secret-masked stream entry construction, and predicate-
based stream queries without any Qt dependency.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
import logging
from typing import Iterable, Mapping

from pypost.core.websocket_transport_protocol import RawFrame

logger = logging.getLogger(__name__)

__all__ = [
    "StreamEntry",
    "StreamQuery",
    "MessageStream",
    "build_stream_entry",
]


@dataclass(frozen=True)
class StreamEntry:
    """Immutable entry in a WebSocket message stream."""

    seq: int
    ts_utc: str
    kind: str
    direction: str
    payload_format: str
    payload: str
    byte_size: int
    truncated: bool = False
    detail: str = ""


@dataclass
class StreamQuery:
    """Filter predicate for WebSocket stream entries."""

    direction: str | None = None
    kind: str | None = None
    payload_format: str | None = None
    search_text: str = ""
    show_heartbeats: bool = False

    def matches(self, entry: StreamEntry) -> bool:
        """Evaluate whether entry satisfies this query filter."""
        if self.direction is not None and entry.direction != self.direction:
            return False
        if self.kind is not None and entry.kind != self.kind:
            return False
        if self.payload_format is not None and entry.payload_format != self.payload_format:
            return False
        if not self.show_heartbeats and entry.kind == "lifecycle":
            detail_lower = entry.detail.lower()
            if "ping" in detail_lower or "pong" in detail_lower or "heartbeat" in detail_lower:
                return False
        if self.search_text:
            query_lower = self.search_text.lower()
            if (
                query_lower not in entry.payload.lower()
                and query_lower not in entry.detail.lower()
            ):
                return False
        return True


class MessageStream:
    """Bounded in-memory stream buffer with dual FIFO eviction and drop counters."""

    def __init__(
        self,
        max_entries: int = 5000,
        memory_budget_bytes: int = 67_108_864,
    ) -> None:
        self._max_entries = max_entries
        self._memory_budget_bytes = memory_budget_bytes
        self._entries: deque[StreamEntry] = deque()
        self._retained_bytes: int = 0
        self._dropped_capacity: int = 0
        self._dropped_memory_budget: int = 0

    def append(self, entry: StreamEntry) -> tuple[int, str | None]:
        """Append entry to stream, evicting oldest entries if limits are exceeded.

        Returns:
            Tuple of (total_evicted_count, primary_eviction_reason_or_None).
        """
        evicted_cap = 0
        evicted_mem = 0
        entry_cost = len(entry.payload.encode("utf-8"))

        while len(self._entries) >= self._max_entries:
            old = self._entries.popleft()
            self._retained_bytes -= len(old.payload.encode("utf-8"))
            self._dropped_capacity += 1
            evicted_cap += 1

        while self._entries and (self._retained_bytes + entry_cost > self._memory_budget_bytes):
            old = self._entries.popleft()
            self._retained_bytes -= len(old.payload.encode("utf-8"))
            self._dropped_memory_budget += 1
            evicted_mem += 1

        self._entries.append(entry)
        self._retained_bytes += entry_cost

        total_evicted = evicted_cap + evicted_mem
        if evicted_cap > 0 and evicted_mem == 0:
            reason = "capacity"
        elif evicted_mem > 0:
            reason = "memory_budget"
        else:
            reason = None

        if total_evicted > 0:
            logger.debug(
                "websocket_stream_eviction_triggered cause=%s evicted_count=%d "
                "retained_entries=%d retained_bytes=%d",
                reason,
                total_evicted,
                len(self._entries),
                self._retained_bytes,
            )

        return total_evicted, reason

    def snapshot(self) -> tuple[StreamEntry, ...]:
        """Return an immutable snapshot of all currently retained entries."""
        return tuple(self._entries)

    def matching(self, query: StreamQuery) -> tuple[int, ...]:
        """Return sequence numbers of all entries matching query."""
        return tuple(entry.seq for entry in self._entries if query.matches(entry))

    def clear(self) -> None:
        """Clear all entries and reset retained bytes and drop counters."""
        self._entries.clear()
        self._retained_bytes = 0
        self._dropped_capacity = 0
        self._dropped_memory_budget = 0
        logger.debug("websocket_stream_cleared")

    @property
    def dropped(self) -> dict[str, int]:
        """Return copy of drop counts per cause."""
        return {
            "capacity": self._dropped_capacity,
            "memory_budget": self._dropped_memory_budget,
        }

    @property
    def total_retained_bytes(self) -> int:
        """Return total bytes of payload retained in the buffer."""
        return self._retained_bytes

    def __len__(self) -> int:
        return len(self._entries)

    def __getitem__(self, index: int) -> StreamEntry:
        return self._entries[index]


def _mask_secrets(
    text: str,
    env_vars: Mapping[str, str] | None = None,
    hidden_keys: Iterable[str] | None = None,
) -> str:
    if not text or not env_vars or not hidden_keys:
        return text
    values = [
        env_vars[k]
        for k in hidden_keys
        if k in env_vars and env_vars[k]
    ]
    for val in sorted(values, key=len, reverse=True):
        text = text.replace(val, "***")
    return text


def build_stream_entry(
    frame: RawFrame | None = None,
    *,
    env_vars: Mapping[str, str] | None = None,
    hidden_keys: Iterable[str] | None = None,
    truncate_bytes: int = 262_144,
    seq: int,
    kind: str = "message",
    direction: str | None = None,
    payload_format: str | None = None,
    payload: str | None = None,
    byte_size: int | None = None,
    detail: str = "",
    ts_utc: str | None = None,
) -> StreamEntry:
    """Construct a masked, display-truncated StreamEntry from frame or explicit data."""
    if direction is not None:
        dir_val = str(direction.value if hasattr(direction, "value") else direction)
    elif frame is not None:
        f_dir = frame.direction
        dir_val = str(f_dir.value if hasattr(f_dir, "value") else f_dir)
    else:
        dir_val = "none"

    if payload_format is not None:
        fmt_val = str(payload_format.value if hasattr(payload_format, "value") else payload_format)
    elif frame is not None:
        f_fmt = frame.payload_format
        fmt_val = str(f_fmt.value if hasattr(f_fmt, "value") else f_fmt)
    else:
        fmt_val = "text"

    if payload is not None:
        raw_text = payload
    elif frame is not None:
        if isinstance(frame.payload, bytes):
            raw_text = frame.payload.decode("utf-8", errors="replace")
        else:
            raw_text = str(frame.payload)
    else:
        raw_text = ""

    if byte_size is not None:
        wire_bytes = byte_size
    elif frame is not None:
        wire_bytes = frame.byte_size
    else:
        wire_bytes = len(raw_text.encode("utf-8"))

    sanitized = _mask_secrets(raw_text, env_vars=env_vars, hidden_keys=hidden_keys)

    if wire_bytes > truncate_bytes:
        truncated = True
        final_payload = sanitized[:truncate_bytes]
    else:
        truncated = False
        final_payload = sanitized

    if ts_utc is not None:
        ts_val = ts_utc
    elif frame is not None:
        ts = frame.timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        ts_utc_dt = ts.astimezone(timezone.utc)
        ts_val = ts_utc_dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    else:
        ts_val = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    sanitized_detail = (
        _mask_secrets(detail, env_vars=env_vars, hidden_keys=hidden_keys)
        if detail
        else ""
    )

    return StreamEntry(
        seq=seq,
        ts_utc=ts_val,
        kind=kind,
        direction=dir_val,
        payload_format=fmt_val,
        payload=final_payload,
        byte_size=wire_bytes,
        truncated=truncated,
        detail=sanitized_detail,
    )
