"""Structured MCP call_tool result pane (content, errors, elapsed time)."""

from __future__ import annotations

import json
import logging
from typing import Any

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pypost.core.sensitive_text_sanitizer import sanitize_text
from pypost.ui.widget_ids import (
    MCP_CLIENT_ELAPSED_LABEL,
    MCP_CLIENT_RESULT_FOLD_ALL_BUTTON,
    MCP_CLIENT_RESULT_PANE,
    MCP_CLIENT_RESULT_UNFOLD_ALL_BUTTON,
    set_widget_id,
)
from pypost.ui.widgets.fold import BodyFormat, detect_body_format
from pypost.ui.widgets.fold.fold_controller import FoldController
from pypost.ui.widgets.foldable_code_view import FoldableCodeView

__all__ = ["McpResultView"]

logger = logging.getLogger(__name__)

_FOLDABLE_FORMATS = (BodyFormat.JSON, BodyFormat.XML, BodyFormat.YAML)


class McpResultView(QWidget):
    """Show CallToolResult content versus errors plus elapsed time."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Result", self))
        self._progress = QLabel("", self)
        header_layout.addWidget(self._progress)
        self._elapsed = QLabel("", self)
        set_widget_id(self._elapsed, MCP_CLIENT_ELAPSED_LABEL)
        header_layout.addWidget(self._elapsed)
        header_layout.addStretch()

        self._fold_all_btn = QPushButton("Fold All", self)
        set_widget_id(self._fold_all_btn, MCP_CLIENT_RESULT_FOLD_ALL_BUTTON)
        self._fold_all_btn.setEnabled(False)
        self._fold_all_btn.clicked.connect(self.fold_all)
        header_layout.addWidget(self._fold_all_btn)

        self._unfold_all_btn = QPushButton("Unfold All", self)
        set_widget_id(self._unfold_all_btn, MCP_CLIENT_RESULT_UNFOLD_ALL_BUTTON)
        self._unfold_all_btn.setEnabled(False)
        self._unfold_all_btn.clicked.connect(self.unfold_all)
        header_layout.addWidget(self._unfold_all_btn)

        layout.addLayout(header_layout)

        self._body = FoldableCodeView(self)
        self._body.setReadOnly(True)
        set_widget_id(self._body, MCP_CLIENT_RESULT_PANE)
        layout.addWidget(self._body, 1)

    def fold_controller(self) -> FoldController:
        """Return the body's fold controller."""
        return self._body.fold_controller()

    def body_format(self) -> BodyFormat:
        """Return the current body format."""
        return self._body.body_format()

    def fold_all(self) -> None:
        """Collapse all fold regions in the result body."""
        logger.debug("mcp_result_folding_fold_all_invoked")
        self._body.fold_all()

    def unfold_all(self) -> None:
        """Expand all fold regions in the result body."""
        logger.debug("mcp_result_folding_unfold_all_invoked")
        self._body.unfold_all()

    def set_in_progress(self) -> None:
        """Replace a stale result with an in-flight placeholder."""
        self._elapsed.setText("")
        self._set_fold_buttons_enabled(False)
        self._body.set_body_format(BodyFormat.PLAIN)
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

        text = sanitize_text("\n".join(lines))
        if is_error:
            fmt = BodyFormat.PLAIN
        else:
            fmt = detect_body_format(None, text)

        logger.debug(
            "mcp_result_folding_format_detected format=%s byte_size=%d",
            fmt.name,
            len(text.encode("utf-8")),
        )

        if fmt == BodyFormat.JSON:
            try:
                parsed = json.loads(text)
                text = json.dumps(parsed, indent=2)
            except Exception:
                pass

        self._body.set_body_format(fmt)
        self._body.setPlainText(text)
        self._body.fold_controller().ensure_scanned()
        self._set_fold_buttons_enabled(fmt in _FOLDABLE_FORMATS and not is_error)

    def set_error(self, message: str, elapsed_s: float | None) -> None:
        """Show a transport or validation error in the result area."""
        self._progress.setText("")
        if elapsed_s is None:
            self._elapsed.setText("")
        else:
            self._set_elapsed(elapsed_s)
        self._set_fold_buttons_enabled(False)
        self._body.set_body_format(BodyFormat.PLAIN)
        self._body.setPlainText(message)

    def clear(self) -> None:
        """Empty the pane (disconnect / teardown / lost selection)."""
        self._progress.setText("")
        self._elapsed.setText("")
        self._set_fold_buttons_enabled(False)
        self._body.set_body_format(BodyFormat.PLAIN)
        self._body.setPlainText("")

    def _set_fold_buttons_enabled(self, enabled: bool) -> None:
        self._fold_all_btn.setEnabled(enabled)
        self._unfold_all_btn.setEnabled(enabled)

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
