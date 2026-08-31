"""WebSocket transcript export formatters and disk writers (PYPOST-1130).

Provides structured JSON array export and formatted Plain Text transcript export
with session drop accounting and atomic file persistence.
"""

from __future__ import annotations

from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Any, Iterable, Mapping

from pypost.core.export_file_writer import write_json_export_file
from pypost.core.sensitive_text_sanitizer import sanitize_text
from pypost.core.websocket_stream import MessageStream, StreamEntry

logger = logging.getLogger(__name__)

__all__ = [
    "StreamExportSnapshot",
    "WebSocketExportError",
    "format_json_transcript",
    "format_text_transcript",
    "export_stream_to_json_file",
    "export_stream_to_text_file",
]


class WebSocketExportError(Exception):
    """Raised when formatting or writing a WebSocket transcript export fails."""


class StreamExportSnapshot:
    """Immutable stream view for off-thread transcript export (PYPOST-1144)."""

    __slots__ = ("_entries", "_dropped")

    def __init__(
        self,
        entries: Iterable[StreamEntry],
        dropped: Mapping[str, int],
    ) -> None:
        self._entries = tuple(entries)
        self._dropped = {
            "capacity": int(dropped.get("capacity", 0)),
            "memory_budget": int(dropped.get("memory_budget", 0)),
        }

    def __len__(self) -> int:
        return len(self._entries)

    def snapshot(self) -> tuple[StreamEntry, ...]:
        return self._entries

    @property
    def dropped(self) -> dict[str, int]:
        return dict(self._dropped)


def format_json_transcript(
    stream: MessageStream | StreamExportSnapshot,
    metadata: Mapping[str, Any] | None = None,
    *,
    env_vars: Mapping[str, str] | None = None,
    hidden_keys: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Format stream entries and metadata as a JSON dictionary with Tier 2 sanitization."""
    exported_at = (
        metadata.get("exported_at")
        if metadata and "exported_at" in metadata
        else datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    )
    meta: dict[str, Any] = {
        "exported_at": exported_at,
        "total_retained": len(stream),
        "dropped": dict(stream.dropped),
    }
    if metadata:
        meta.update(metadata)

    entries = [
        {
            "seq": e.seq,
            "ts_utc": e.ts_utc,
            "kind": e.kind,
            "direction": e.direction,
            "payload_format": e.payload_format,
            "payload": sanitize_text(e.payload, env_vars=env_vars, hidden_keys=hidden_keys),
            "byte_size": e.byte_size,
            "truncated": e.truncated,
            "detail": (
                sanitize_text(e.detail, env_vars=env_vars, hidden_keys=hidden_keys)
                if e.detail
                else ""
            ),
        }
        for e in stream.snapshot()
    ]
    return {
        "schema_version": "1.0",
        "metadata": meta,
        "entries": entries,
    }


def format_text_transcript(
    stream: MessageStream | StreamExportSnapshot,
    metadata: Mapping[str, Any] | None = None,
    *,
    env_vars: Mapping[str, str] | None = None,
    hidden_keys: Iterable[str] | None = None,
) -> str:
    """Format stream entries as a human-readable text transcript with Tier 2 sanitization."""
    exported_at = (
        metadata.get("exported_at")
        if metadata and "exported_at" in metadata
        else datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    )
    lines = [
        "# PyPost WebSocket Transcript",
        f"# Exported: {exported_at}",
        f"# Retained entries: {len(stream)}",
        f"# Dropped entries: capacity={stream.dropped['capacity']}, "
        f"memory_budget={stream.dropped['memory_budget']}",
        "# ----------------------------------------------------------------------",
    ]
    for e in stream.snapshot():
        parts = [f"[{e.ts_utc}]", f"[{e.direction}]", f"[{e.byte_size}B]"]
        if e.truncated:
            parts.append("[TRUNCATED]")
        if e.kind == "lifecycle":
            parts.append("[lifecycle]")
            content = e.detail or e.payload
        else:
            content = e.payload
        if content:
            sanitized_content = sanitize_text(content, env_vars=env_vars, hidden_keys=hidden_keys)
            parts.append(sanitized_content)
        lines.append(" ".join(parts))
    return "\n".join(lines) + "\n"


def export_stream_to_json_file(
    path: Path,
    stream: MessageStream | StreamExportSnapshot,
    metadata: Mapping[str, Any] | None = None,
    *,
    env_vars: Mapping[str, str] | None = None,
    hidden_keys: Iterable[str] | None = None,
) -> None:
    """Export stream to a JSON transcript file on disk with Tier 2 sanitization."""
    payload = format_json_transcript(
        stream, metadata=metadata, env_vars=env_vars, hidden_keys=hidden_keys
    )
    write_json_export_file(path, payload, error_cls=WebSocketExportError)
    logger.info(
        "websocket_stream_json_exported path=%s entries_count=%d "
        "capacity_dropped=%d memory_budget_dropped=%d",
        path,
        len(stream),
        stream.dropped["capacity"],
        stream.dropped["memory_budget"],
    )


def export_stream_to_text_file(
    path: Path,
    stream: MessageStream | StreamExportSnapshot,
    metadata: Mapping[str, Any] | None = None,
    *,
    env_vars: Mapping[str, str] | None = None,
    hidden_keys: Iterable[str] | None = None,
) -> None:
    """Export stream to a UTF-8 plain text transcript file with Tier 2 sanitization."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        content = format_text_transcript(
            stream, metadata=metadata, env_vars=env_vars, hidden_keys=hidden_keys
        )
        path.write_text(content, encoding="utf-8")
        logger.info(
            "websocket_stream_text_exported path=%s entries_count=%d "
            "capacity_dropped=%d memory_budget_dropped=%d",
            path,
            len(stream),
            stream.dropped["capacity"],
            stream.dropped["memory_budget"],
        )
    except (OSError, TypeError, ValueError) as exc:
        raise WebSocketExportError(f"Could not write transcript file: {exc}") from exc
