"""Interactive click-to-reveal response masking controller for GUI ResponseView.

Implements MASK-3 requirements:
- MaskedTokenSpan tracking character ranges in QTextDocument.
- JsonMaskFormatter for AST/structural masking and span discovery.
- ResponseMaskController for ExtraSelection styling, hover cursors, and click toggling.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Sequence

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QColor, QMouseEvent, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QTextEdit, QToolTip

from pypost.core.sensitive_text_sanitizer import format_path_variants

if TYPE_CHECKING:
    from pypost.ui.widgets.foldable_code_view import FoldableCodeView

logger = logging.getLogger(__name__)


@dataclass
class MaskedTokenSpan:
    """Tracks coordinates and state of a masked token in the text document."""

    start_pos: int
    end_pos: int
    raw_value: str
    masked_value: str = '"***"'
    is_revealed: bool = False
    path: str = ""


class JsonMaskFormatter:
    """Formats JSON with indentation while detecting and recording masked token spans."""

    def __init__(self, selectors: set[str], indent: int = 2) -> None:
        self.selectors = {
            s.strip()
            for s in selectors
            if s and s.strip() and not s.strip().lower().startswith("header:")
        }
        self.indent = indent
        self._chunks: list[str] = []
        self._spans: list[MaskedTokenSpan] = []

    def _emit(self, text: str) -> None:
        self._chunks.append(text)

    def _current_offset(self) -> int:
        return sum(len(c) for c in self._chunks)

    def format(self, node: Any) -> tuple[str, list[MaskedTokenSpan]]:
        self._chunks = []
        self._spans = []
        self._format_value(node, [], 0)
        return "".join(self._chunks), self._spans

    def _format_value(self, node: Any, path: list[str], depth: int) -> None:
        if isinstance(node, dict):
            self._format_dict(node, path, depth)
        elif isinstance(node, list):
            self._format_list(node, path, depth)
        else:
            self._emit(json.dumps(node, ensure_ascii=False))

    def _format_dict(self, node: dict[str, Any], path: list[str], depth: int) -> None:
        if not node:
            self._emit("{}")
            return
        self._emit("{\n")
        items = list(node.items())
        for idx, (key, val) in enumerate(items):
            key_str = str(key)
            self._emit(" " * ((depth + 1) * self.indent))
            self._emit(json.dumps(key_str, ensure_ascii=False) + ": ")
            variants = format_path_variants(path, key_str)
            if any(var in self.selectors for var in variants):
                masked_val = '"***"'
                raw_val = json.dumps(val, indent=self.indent, ensure_ascii=False)
                start_pos = self._current_offset()
                self._emit(masked_val)
                end_pos = self._current_offset()
                self._spans.append(
                    MaskedTokenSpan(
                        start_pos=start_pos,
                        end_pos=end_pos,
                        raw_value=raw_val,
                        masked_value=masked_val,
                        is_revealed=False,
                        path=".".join(path + [key_str]),
                    )
                )
            else:
                self._format_value(val, path + [key_str], depth + 1)
            if idx < len(items) - 1:
                self._emit(",")
            self._emit("\n")
        self._emit(" " * (depth * self.indent) + "}")

    def _format_list(self, node: list[Any], path: list[str], depth: int) -> None:
        if not node:
            self._emit("[]")
            return
        self._emit("[\n")
        for idx, item in enumerate(node):
            self._emit(" " * ((depth + 1) * self.indent))
            self._format_value(item, path + ["*"], depth + 1)
            if idx < len(node) - 1:
                self._emit(",")
            self._emit("\n")
        self._emit(" " * (depth * self.indent) + "]")


def format_masked_json(
    raw_json: str,
    hidden_fields: Sequence[str],
    indent: int = 2,
) -> tuple[str, list[MaskedTokenSpan]]:
    """Parses JSON and returns pretty-printed text with masked placeholders and token spans."""
    parsed = json.loads(raw_json)
    if not isinstance(parsed, (dict, list)):
        return json.dumps(parsed, indent=indent, ensure_ascii=False), []

    formatter = JsonMaskFormatter(set(hidden_fields), indent=indent)
    return formatter.format(parsed)


class ResponseMaskController(QObject):
    """Coordinates masked token spans, hover cursors, and click-to-reveal toggling."""

    def __init__(
        self,
        code_view: FoldableCodeView,
        response_view: Any = None,
    ) -> None:
        super().__init__(code_view)
        self.code_view = code_view
        self.response_view = response_view
        self._spans: list[MaskedTokenSpan] = []
        self._force_viewport_clicks: bool = False

        self.code_view.viewport().installEventFilter(self)
        self.code_view.viewport().setMouseTracking(True)
        if hasattr(self.code_view, "set_mask_controller"):
            self.code_view.set_mask_controller(self)

    def clear(self) -> None:
        """Clears all tracked spans and visual highlights."""
        self._spans.clear()
        self.update_visual_formats()
        if self.code_view and self.code_view.viewport():
            self.code_view.viewport().setCursor(Qt.CursorShape.IBeamCursor)
        QToolTip.hideText()

    def set_masked_spans(self, spans: list[MaskedTokenSpan]) -> None:
        """Stores token spans and applies initial ExtraSelection highlights."""
        self._spans = list(spans)
        self.update_visual_formats()
        logger.debug("response_masking_spans_updated span_count=%d", len(self._spans))

    def spans(self) -> list[MaskedTokenSpan]:
        """Returns the list of tracked token spans."""
        return self._spans

    def span_at(self, char_pos: int) -> MaskedTokenSpan | None:
        """Finds the token span containing the specified character position."""
        for span in self._spans:
            if span.start_pos <= char_pos <= span.end_pos:
                return span
        return None

    def handle_click(self, char_pos: int) -> bool:
        """Toggles a masked span at char_pos between masked and revealed states."""
        span = self.span_at(char_pos)
        if span is None:
            return False

        old_len = span.end_pos - span.start_pos
        new_text = span.raw_value if not span.is_revealed else span.masked_value
        span.is_revealed = not span.is_revealed

        cursor = QTextCursor(self.code_view.document())
        cursor.setPosition(span.start_pos)
        cursor.setPosition(span.end_pos, QTextCursor.MoveMode.KeepAnchor)
        cursor.insertText(new_text)

        delta = len(new_text) - old_len
        span.end_pos = span.start_pos + len(new_text)

        for other in self._spans:
            if other.start_pos > span.start_pos:
                other.start_pos += delta
                other.end_pos += delta

        self.update_visual_formats()
        self.code_view.fold_controller().ensure_scanned()

        if self.response_view is not None and hasattr(self.response_view, "search_input"):
            if self.response_view.search_input.text():
                if hasattr(self.response_view, "_on_search_text_changed"):
                    self.response_view._on_search_text_changed()

        logger.debug(
            "click_to_reveal_toggle path=%s revealed=%s",
            span.path,
            span.is_revealed,
        )

        return True

    def update_visual_formats(self) -> None:
        """Applies ExtraSelection styling to indicate clickable masked/revealed spans."""
        if not self._spans:
            self.code_view.setExtraSelections([])
            return

        selections: list[QTextEdit.ExtraSelection] = []
        for span in self._spans:
            sel = QTextEdit.ExtraSelection()
            cursor = QTextCursor(self.code_view.document())
            cursor.setPosition(span.start_pos)
            cursor.setPosition(span.end_pos, QTextCursor.MoveMode.KeepAnchor)
            sel.cursor = cursor

            fmt = QTextCharFormat()
            if span.is_revealed:
                fmt.setBackground(QColor(76, 175, 80, 40))
                fmt.setUnderlineStyle(QTextCharFormat.UnderlineStyle.DotLine)
                fmt.setToolTip("Click to re-mask")
            else:
                fmt.setBackground(QColor(128, 128, 128, 48))
                fmt.setUnderlineStyle(QTextCharFormat.UnderlineStyle.DashUnderline)
                fmt.setToolTip("Click to reveal")
            sel.format = fmt
            selections.append(sel)

        self.code_view.setExtraSelections(selections)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """Filters viewport mouse events for hover cursors, tooltips, and click-to-reveal."""
        if self.code_view and watched is self.code_view.viewport():
            if event.type() == QEvent.Type.MouseMove and isinstance(event, QMouseEvent):
                pos = event.position().toPoint()
                char_pos = self.code_view.cursorForPosition(pos).position()
                span = self.span_at(char_pos)
                if span is not None:
                    self.code_view.viewport().setCursor(Qt.CursorShape.PointingHandCursor)
                    tooltip_text = "Click to re-mask" if span.is_revealed else "Click to reveal"
                    QToolTip.showText(
                        event.globalPosition().toPoint(),
                        tooltip_text,
                        self.code_view.viewport(),
                    )
                else:
                    self.code_view.viewport().setCursor(Qt.CursorShape.IBeamCursor)
                    QToolTip.hideText()
            elif event.type() == QEvent.Type.MouseButtonRelease and isinstance(event, QMouseEvent):
                if (
                    event.button() == Qt.MouseButton.LeftButton
                    and (self.code_view.isVisible() or self._force_viewport_clicks)
                ):
                    if not self.code_view.textCursor().hasSelection():
                        pos = event.position().toPoint()
                        char_pos = self.code_view.cursorForPosition(pos).position()
                        if self.handle_click(char_pos):
                            return True
            elif event.type() == QEvent.Type.Leave:
                self.code_view.viewport().setCursor(Qt.CursorShape.IBeamCursor)
                QToolTip.hideText()

        return super().eventFilter(watched, event)
