"""Structured MCP call_tool result pane (content, errors, elapsed time)."""

from __future__ import annotations

import json
from typing import Any

from PySide6.QtWidgets import QLabel, QPlainTextEdit, QVBoxLayout, QWidget

from pypost.core.sensitive_text_sanitizer import sanitize_text
from pypost.ui.widget_ids import (
    MCP_CLIENT_ELAPSED_LABEL,
    MCP_CLIENT_RESULT_PANE,
    set_widget_id,
)

__all__ = ["McpResultView"]


class McpResultView(QWidget):
    """Show CallToolResult content versus errors plus elapsed time."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(QLabel("Result", self))
        self._progress = QLabel("", self)
        layout.addWidget(self._progress)
        self._elapsed = QLabel("", self)
        set_widget_id(self._elapsed, MCP_CLIENT_ELAPSED_LABEL)
        layout.addWidget(self._elapsed)
        self._body = QPlainTextEdit(self)
        self._body.setReadOnly(True)
        set_widget_id(self._body, MCP_CLIENT_RESULT_PANE)
        layout.addWidget(self._body, 1)

    def set_in_progress(self) -> None:
        """Replace a stale result with an in-flight placeholder."""
        self._elapsed.setText("")
        self._body.setPlainText("")
        self._progress.setText("Invoking...")

    def set_result(
        self,
        payload: dict[str, Any],
        elapsed_s: float,
        *,
        is_error: bool,
    ) -> None:
        """Render content blocks and optional structuredContent."""
        self._progress.setText("")
        self._set_elapsed(elapsed_s)
        lines: list[str] = []
        if is_error:
            lines.append("Error")
        lines.extend(_content_lines(payload.get("content")))
        structured = payload.get("structuredContent")
        if structured is not None:
            lines.append("structuredContent:")
            lines.append(json.dumps(structured, indent=2))
        if len(lines) == 1 and is_error:
            lines.append(json.dumps(payload, indent=2))
        elif not lines:
            lines.append(json.dumps(payload, indent=2))
        self._body.setPlainText(sanitize_text("\n".join(lines)))

    def set_error(self, message: str, elapsed_s: float | None) -> None:
        """Show a transport or validation error in the result area."""
        self._progress.setText("")
        if elapsed_s is None:
            self._elapsed.setText("")
        else:
            self._set_elapsed(elapsed_s)
        self._body.setPlainText(message)

    def clear(self) -> None:
        """Empty the pane (disconnect / teardown / lost selection)."""
        self._progress.setText("")
        self._elapsed.setText("")
        self._body.setPlainText("")

    def _set_elapsed(self, elapsed_s: float) -> None:
        self._elapsed.setText(f"Elapsed: {elapsed_s:g} s")


def _content_lines(content: object) -> list[str]:
    if not isinstance(content, list):
        return []
    lines: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        block_type = block.get("type")
        if block_type == "text":
            lines.append(sanitize_text(str(block.get("text") or "")))
            continue
        if block_type in {"image", "audio"}:
            lines.append(f"[{block_type} content]")
            continue
        lines.append(sanitize_text(json.dumps(block)))
    return lines
