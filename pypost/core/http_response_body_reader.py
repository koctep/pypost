"""Streamed HTTP response body reader with optional byte cap."""

from __future__ import annotations

from typing import Callable


def read_streamed_body(
    response,
    *,
    max_response_bytes: int,
    stream_callback: Callable[[str], None] | None = None,
    stop_flag: Callable[[], bool] | None = None,
) -> tuple[str, bool]:
    """Read iter_content chunks; return (decoded text, truncated)."""
    content_parts: list[str] = []
    total_bytes = 0
    truncated = False

    for chunk in response.iter_content(chunk_size=None):
        if stop_flag and stop_flag():
            response.close()
            break
        if not chunk:
            continue

        raw = chunk if isinstance(chunk, bytes) else chunk.encode("utf-8")
        if max_response_bytes > 0 and total_bytes + len(raw) > max_response_bytes:
            allowed = max_response_bytes - total_bytes
            raw = raw[:allowed]
            truncated = True
        total_bytes += len(raw)
        text = raw.decode("utf-8", errors="replace")
        content_parts.append(text)
        if stream_callback:
            stream_callback(text)
        if truncated:
            response.close()
            break
        if stop_flag and stop_flag():
            response.close()
            break

    return "".join(content_parts), truncated
