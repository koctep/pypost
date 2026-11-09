"""Interactive click-to-reveal response masking controller for GUI ResponseView.

Implements MASK-3 requirements:
- MaskedTokenSpan tracking character ranges in QTextDocument.
- JsonMaskFormatter for AST/structural masking and span discovery.
- ResponseMaskController for ExtraSelection styling, hover cursors, and click toggling.
"""

from __future__ import annotations

import json
import logging
from bisect import bisect_right
from dataclasses import dataclass
from operator import attrgetter
from typing import TYPE_CHECKING, Any, Sequence

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QColor, QMouseEvent, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QTextEdit, QToolTip

from pypost.core.json_selector_engine import JsonSelectorEngine

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

    def __init__(self, selectors: set[str] | Sequence[str], indent: int = 2) -> None:
        self.engine = JsonSelectorEngine(selectors)
        self.selectors = set(self.engine._raw_selectors)
        self.indent = indent
        self._chunks: list[str] = []
        self._spans: list[MaskedTokenSpan] = []
        self._current_pos: int = 0

    def _emit(self, text: str) -> None:
        self._chunks.append(text)
        self._current_pos += len(text)

    def _current_offset(self) -> int:
        return self._current_pos

    def format(self, node: Any) -> tuple[str, list[MaskedTokenSpan]]:
        self._chunks = []
        self._spans = []
        self._current_pos = 0
        path: list[str] = []
        self._format_value(node, path, 0)
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
            if self.engine.matches(path, key_str):
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
                        path=self.engine.canonical_path(path, key_str),
                    )
                )
            else:
                path.append(key_str)
                try:
                    self._format_value(val, path, depth + 1)
                finally:
                    path.pop()
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
            path.append("*")
            try:
                self._format_value(item, path, depth + 1)
            finally:
                path.pop()
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
        self._reveal_state: dict[str, bool] = {}
        self._force_viewport_clicks: bool = False

        self.code_view.viewport().installEventFilter(self)
        self.code_view.viewport().setMouseTracking(True)
        if hasattr(self.code_view, "set_mask_controller"):
            self.code_view.set_mask_controller(self)

    def clear(self) -> None:
        """Clears tracked spans, reveal memory, and visual highlights."""
        memory_size = len(self._reveal_state)
        self._spans.clear()
        self._reveal_state.clear()
        self.update_visual_formats()
        if self.code_view and self.code_view.viewport():
            self.code_view.viewport().setCursor(Qt.CursorShape.IBeamCursor)
        QToolTip.hideText()
        logger.debug("reveal_state_cleared memory_size=%d", memory_size)

    def clear_spans(self) -> None:
        """Clears tracked spans and visuals but keeps path-keyed reveal memory."""
        self._spans.clear()
        self.update_visual_formats()
        if self.code_view and self.code_view.viewport():
            self.code_view.viewport().setCursor(Qt.CursorShape.IBeamCursor)
        QToolTip.hideText()
        logger.debug(
            "reveal_state_spans_cleared memory_size=%d",
            len(self._reveal_state),
        )

    def set_masked_spans(self, spans: list[MaskedTokenSpan]) -> None:
        """Stores token spans, restores persisted reveals, and applies highlights."""
        self._spans = list(spans)
        restored = self._apply_persisted_reveals()
        self.update_visual_formats()
        logger.debug(
            "response_masking_spans_updated span_count=%d restored_reveals=%d memory_size=%d",
            len(self._spans),
            restored,
            len(self._reveal_state),
        )

    def _apply_persisted_reveals(self) -> int:
        """Expand document text for spans whose path was previously revealed.

        Returns:
            Number of spans restored to the revealed presentation state.
        """
        if not self._reveal_state or not self._spans:
            return 0
        restored = 0
        for span in self._spans:
            if not span.path or span.is_revealed:
                continue
            if not self._reveal_state.get(span.path, False):
                continue
            old_len = span.end_pos - span.start_pos
            new_text = span.raw_value
            span.is_revealed = True
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
            restored += 1
        if restored:
            logger.debug(
                "reveal_state_restored restored_count=%d memory_size=%d",
                restored,
                len(self._reveal_state),
            )
        return restored

    def spans(self) -> list[MaskedTokenSpan]:
        """Returns the list of tracked token spans."""
        return self._spans

    def span_at(self, char_pos: int) -> MaskedTokenSpan | None:
        """Finds the token span containing the specified character position.

        Uses ``bisect_right`` on ascending ``start_pos`` so that
        ``idx - 1`` is the rightmost span with ``start_pos <= char_pos``
        (including exact start hits). Coverage remains inclusive on both
        ends: ``start_pos <= char_pos <= end_pos``.
        """
        if not self._spans:
            return None
        idx = bisect_right(self._spans, char_pos, key=attrgetter("start_pos"))
        if idx == 0:
            return None
        candidate = self._spans[idx - 1]
        if char_pos <= candidate.end_pos:
            return candidate
        return None

    def handle_click(self, char_pos: int) -> bool:
        """Toggles a masked span at char_pos between masked and revealed states."""
        span = self.span_at(char_pos)
        if span is None:
            return False

        old_len = span.end_pos - span.start_pos
        new_text = span.raw_value if not span.is_revealed else span.masked_value
        span.is_revealed = not span.is_revealed
        if span.path:
            self._reveal_state[span.path] = span.is_revealed

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
