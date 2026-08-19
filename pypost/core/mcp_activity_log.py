"""In-memory ring buffer of recent inbound MCP server operations (PYPOST-141)."""

from __future__ import annotations

import logging
import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from pypost.core.sensitive_text_sanitizer import sanitize_text

logger = logging.getLogger(__name__)

DEFAULT_MAX_ENTRIES = 100


@dataclass(frozen=True)
class McpActivityEntry:
    """One recorded MCP server operation for UI inspection."""

    id: str
    timestamp: datetime
    operation: str  # "list_tools" | "call_tool"
    outcome: str  # "success" | "error"
    tool_name: str | None = None
    tool_count: int | None = None
    mcp_arg_count: int | None = None
    http_status: int | None = None
    detail: str | None = None
    duration_ms: float | None = None

    @property
    def details(self) -> str | None:
        return self.detail

    @staticmethod
    def _sanitize_detail(detail: str | None) -> str | None:
        if detail is None:
            return None
        return sanitize_text(detail)

    @staticmethod
    def new_list_tools(tool_count: int) -> McpActivityEntry:
        return McpActivityEntry(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            operation="list_tools",
            outcome="success",
            tool_count=tool_count,
        )

    @staticmethod
    def new_call_tool(
        tool_name: str,
        *,
        outcome: str,
        mcp_arg_count: int,
        http_status: int | None = None,
        detail: str | None = None,
        duration_ms: float | None = None,
    ) -> McpActivityEntry:
        return McpActivityEntry(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            operation="call_tool",
            outcome=outcome,
            tool_name=tool_name,
            mcp_arg_count=mcp_arg_count,
            http_status=http_status,
            detail=McpActivityEntry._sanitize_detail(detail),
            duration_ms=duration_ms,
        )


class McpActivityLog:
    """Thread-safe ring buffer of recent MCP activity with optional append callback."""

    def __init__(
        self,
        max_entries: int = DEFAULT_MAX_ENTRIES,
        on_append: Callable[[McpActivityEntry], None] | None = None,
    ) -> None:
        self._max_entries = max(1, max_entries)
        self._entries: list[McpActivityEntry] = []
        self._lock = threading.Lock()
        self._on_append = on_append

    def append(self, entry: McpActivityEntry) -> None:
        with self._lock:
            self._entries.append(entry)
            if len(self._entries) > self._max_entries:
                overflow = len(self._entries) - self._max_entries
                del self._entries[:overflow]
        logger.info(
            "mcp_activity_recorded operation=%s outcome=%s tool_name=%s tool_count=%s "
            "mcp_arg_count=%s http_status=%s duration_ms=%s",
            entry.operation,
            entry.outcome,
            entry.tool_name,
            entry.tool_count,
            entry.mcp_arg_count,
            entry.http_status,
            entry.duration_ms,
        )
        if self._on_append is not None:
            self._on_append(entry)

    def get_entries(self) -> list[McpActivityEntry]:
        with self._lock:
            return list(reversed(self._entries))

    def count(self) -> int:
        with self._lock:
            return len(self._entries)

    def clear(self) -> None:
        with self._lock:
            removed = len(self._entries)
            self._entries.clear()
        if removed:
            logger.info("mcp_activity_cleared count=%d", removed)
