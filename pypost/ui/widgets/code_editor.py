from __future__ import annotations

import json
import logging
import re

from PySide6.QtCore import QEvent, QMimeData, Qt, QRect
from PySide6.QtGui import (
    QFontMetrics,
    QKeyEvent,
    QMouseEvent,
    QPaintEvent,
    QPainter,
    QTextCursor,
)
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QPlainTextEdit

from pypost.core.yaml_json_converter import convert_json_object_to_yaml
from pypost.core.metrics_protocol import MetricsTrackerProtocol, resolve_metrics
from pypost.ui.widgets.fold import BodyFormat, FoldController
from pypost.ui.widgets.line_number_area import LineNumberArea
from pypost.ui.widgets.validate import ValidationController
from pypost.ui.widgets.paste_json_worker import PasteJsonFormatWorker
from pypost.ui.widgets.variable_aware_widgets import VariableAwarePlainTextEdit
from pypost.ui.widgets.variable_autocomplete_line_edit import reference_statuses

logger = logging.getLogger(__name__)

_CHEVRON_WIDTH = 14
_CHEVRON_PADDING = 2
_PASTE_JSON_FORMAT_CHAR_THRESHOLD = 100 * 1024


def _should_format_pasted_json(text: str) -> bool:
    """Return False when paste-time JSON parse/format would risk UI lag."""
    return len(text) <= _PASTE_JSON_FORMAT_CHAR_THRESHOLD


def _looks_like_json(text: str) -> bool:
    """Heuristic to avoid background work on obviously non-JSON large pastes."""
    stripped = text.lstrip()
    return stripped.startswith("{") or stripped.startswith("[")


class CodeEditor(VariableAwarePlainTextEdit):
    def __init__(
        self,
        parent=None,
        indent_size=2,
        metrics: MetricsTrackerProtocol | None = None,
    ):
        super().__init__(parent)
        self._autocomplete_metrics = resolve_metrics(metrics)
        self._autocomplete_context = "body"
        self.indent_size = indent_size
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        self._body_format = BodyFormat.JSON
        self._yaml_as_json = False
        self._fold_controller = FoldController(self, self._body_format)
        self._validation_controller = ValidationController(self, self._body_format)

        self._line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self._update_line_number_area_width(0)

        self.update_indent_size(indent_size)

        self._paste_json_generation = 0
        self._paste_json_worker: PasteJsonFormatWorker | None = None
        self._async_paste_start = 0
        self._async_paste_length = 0
        self._async_paste_original = ""
        self._autocomplete_popup = QListWidget(self)
        self._autocomplete_popup.setWindowFlags(
            Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint
        )
        self._autocomplete_popup.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._autocomplete_popup.itemClicked.connect(self._apply_body_completion_item)
        self.textChanged.connect(self._refresh_body_feedback)

    def fold_controller(self) -> FoldController:
        return self._fold_controller

    def validation_controller(self) -> ValidationController:
        return self._validation_controller

    def complete_at_cursor(self, text: str, cursor_offset: int):
        prefix = text[:cursor_offset]
        match = re.search(r"\{\{\s*[A-Za-z0-9_]*$", prefix)
        if not match or not self._variables:
            return None
        token = prefix[match.start():]
        token = re.sub(r"^\{\{\s*", "", token).lower()
        candidate = next(
            (name for name in sorted(self._variables) if name.lower().startswith(token)),
            None,
        )
        if candidate is None:
            return None
        return match.start(), cursor_offset, f"{{{{ {candidate} }}}}"

    def show_reference_feedback(self, statuses) -> None:
        self._reference_feedback = list(statuses)
        self.setToolTip("\n".join(status["message"] for status in statuses))

    def _refresh_body_feedback(self) -> None:
        self.refresh_reference_status(self.toPlainText())

    def _update_body_popup(self) -> None:
        result = self.complete_at_cursor(self.toPlainText(), self.textCursor().position())
        self._autocomplete_popup.clear()
        if result is None:
            self._autocomplete_popup.hide()
            return
        prefix = self.toPlainText()[: self.textCursor().position()]
        token = re.sub(r"^\{\{\s*", "", prefix[result[0]:]).lower()
        candidates = [name for name in sorted(self._variables)
                      if name.lower().startswith(token)]
        if not candidates:
            self._autocomplete_popup.hide()
            return
        self._autocomplete_popup.addItems(candidates)
        self._autocomplete_popup.setCurrentRow(0)
        self._autocomplete_popup.move(self.mapToGlobal(self.rect().bottomLeft()))
        self._autocomplete_popup.resize(
            max(self.width(), 180), min(160, 24 * len(candidates) + 8)
        )
        self._autocomplete_popup.show()
        self._autocomplete_metrics.track_gui_variable_autocomplete_trigger(
            self._autocomplete_context
        )

    def _apply_body_completion_item(self, item: QListWidgetItem) -> None:
        self._autocomplete_metrics.track_gui_variable_autocomplete_selection(
            self._autocomplete_context
        )
        result = self.complete_at_cursor(self.toPlainText(), self.textCursor().position())
        if result is None:
            return
        start, end, replacement = result
        cursor = self.textCursor()
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        cursor.insertText(replacement)
        self.setTextCursor(cursor)
        self._autocomplete_popup.hide()

    def _complete_body_key(self, event: QKeyEvent) -> bool:
        if not self._autocomplete_popup.isVisible():
            return False
        if event.key() in (Qt.Key.Key_Down, Qt.Key.Key_Up):
            count = self._autocomplete_popup.count()
            delta = 1 if event.key() == Qt.Key.Key_Down else -1
            self._autocomplete_popup.setCurrentRow(
                (self._autocomplete_popup.currentRow() + delta) % count
            )
            return True
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Tab):
            item = self._autocomplete_popup.currentItem()
            if item:
                self._apply_body_completion_item(item)
            return True
        if event.key() == Qt.Key.Key_Escape:
            self._autocomplete_popup.hide()
            return True
        return False

    def refresh_reference_status(self, text: str) -> None:
        statuses = reference_statuses(text, self._variables)
        self.show_reference_feedback(statuses)
        self._track_reference_feedback(statuses)

    def set_variables(self, variables: dict[str, str]) -> None:
        super().set_variables(variables)
        self._autocomplete_metrics.track_gui_variable_autocomplete_environment_refresh(
            self._autocomplete_context
        )

    def set_body_format(self, body_format: BodyFormat) -> None:
        self._body_format = body_format
        self._fold_controller.set_body_format(body_format)
        self._validation_controller.set_body_format(body_format)
        self._update_line_number_area_width(0)

    def set_yaml_as_json(self, enabled: bool) -> None:
        self._yaml_as_json = enabled

    def setPlainText(self, text: str) -> None:
        self._fold_controller.expand_all()
        super().setPlainText(text)
        self._validation_controller.clear()

    def _refresh_font_metrics(self) -> None:
        """Recalculate tab stops and gutter from the current document font."""
        font_metrics = QFontMetrics(self.document().defaultFont())
        self.setTabStopDistance(self.indent_size * font_metrics.horizontalAdvance(" "))
        self._update_line_number_area_width(0)

    def update_indent_size(self, new_size: int):
        self.indent_size = new_size
        self._refresh_font_metrics()

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.FontChange:
            self._refresh_font_metrics()

    def line_number_area_width(self) -> int:
        digits = max(1, len(str(self.blockCount())))
        font_metrics = QFontMetrics(self.document().defaultFont())
        number_width = font_metrics.horizontalAdvance("9") * digits
        return _CHEVRON_WIDTH + _CHEVRON_PADDING + 3 + number_width

    def chevron_width(self) -> int:
        return _CHEVRON_WIDTH

    def _update_line_number_area_width(self, _block_count: int):
        width = self.line_number_area_width()
        self.setViewportMargins(width, 0, 0, 0)
        cr = self.contentsRect()
        if cr.height() > 0:
            self._line_number_area.setGeometry(QRect(cr.left(), cr.top(), width, cr.height()))

    def _update_line_number_area(self, rect: QRect, dy: int):
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(
                0, rect.y(), self._line_number_area.width(), rect.height()
            )

        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )
        self._validation_controller.layout_error_banner()

    def line_number_area_paint_event(self, event: QPaintEvent):
        painter = QPainter(self._line_number_area)
        painter.fillRect(event.rect(), self.palette().color(self.backgroundRole()))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(
            self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        )
        bottom = top + round(self.blockBoundingRect(block).height())

        gutter_color = self.palette().color(self.foregroundRole())
        gutter_color.setAlpha(128)
        painter.setPen(gutter_color)

        number_left = _CHEVRON_WIDTH + _CHEVRON_PADDING

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                region = self._fold_controller.fold_header_at_block(block_number)
                if region is not None:
                    chevron = (
                        "\u25b6"
                        if self._fold_controller.is_collapsed(region.region_id)
                        else "\u25bc"
                    )
                    painter.drawText(
                        0,
                        top,
                        _CHEVRON_WIDTH,
                        self.fontMetrics().height(),
                        Qt.AlignmentFlag.AlignCenter,
                        chevron,
                    )

                number = str(block_number + 1)
                painter.drawText(
                    number_left,
                    top,
                    self._line_number_area.width() - number_left - 3,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    number,
                )

            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1

    def line_number_area_mouse_press(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        event.accept()

        y = event.position().y()
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(
            self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        )
        bottom = top + round(self.blockBoundingRect(block).height())

        while block.isValid():
            if block.isVisible() and top <= y <= bottom:
                if event.position().x() <= _CHEVRON_WIDTH:
                    region = self._fold_controller.fold_header_at_block(block_number)
                    if region is not None:
                        self._fold_controller.toggle(region.region_id)
                        self._line_number_area.update()
                return

            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1

    def reformat_text(self):
        """Reformat current text with new indent size."""
        text = self.toPlainText()
        if not text:
            return

        try:
            parsed = json.loads(text)
            formatted_json = json.dumps(parsed, indent=self.indent_size)
            self.setPlainText(formatted_json)
        except (json.JSONDecodeError, ValueError):
            pass

    def keyPressEvent(self, event: QKeyEvent):
        if self._complete_body_key(event):
            event.accept()
            return
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._handle_enter_key(event)
        elif event.text() in ("}", "]"):
            self._handle_closing_bracket(event)
        else:
            super().keyPressEvent(event)
        self._update_body_popup()

    def _handle_enter_key(self, event: QKeyEvent):
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.LineUnderCursor)
        line_text = cursor.selectedText()

        indent = ""
        for char in line_text:
            if char.isspace():
                indent += char
            else:
                break

        trimmed_line = line_text.rstrip()
        if trimmed_line and trimmed_line[-1] in ("{", "["):
            indent += " " * self.indent_size

        self.insertPlainText("\n" + indent)

    def _should_outdent_for_closing_bracket(self, line_text: str, column: int) -> bool:
        """True when only whitespace surrounds the cursor on this line."""
        prefix = line_text[:column]
        suffix = line_text[column:]
        if prefix.strip() or suffix.strip():
            return False
        leading_spaces = len(line_text) - len(line_text.lstrip(" "))
        return leading_spaces >= self.indent_size

    def _outdent_line_start(self, cursor: QTextCursor) -> None:
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cursor.movePosition(
            QTextCursor.MoveOperation.Right,
            QTextCursor.MoveMode.KeepAnchor,
            self.indent_size,
        )
        if cursor.selectedText() != " " * self.indent_size:
            return

        cursor.removeSelectedText()
        line_text = cursor.block().text()
        if not line_text.strip():
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
            cursor.movePosition(
                QTextCursor.MoveOperation.Right,
                QTextCursor.MoveMode.MoveAnchor,
                len(line_text),
            )
        self.setTextCursor(cursor)

    def _handle_closing_bracket(self, event: QKeyEvent):
        cursor = self.textCursor()
        block = cursor.block()
        line_text = block.text()
        column = cursor.positionInBlock()

        if self._should_outdent_for_closing_bracket(line_text, column):
            self._outdent_line_start(cursor)

        super().keyPressEvent(event)

    def insertFromMimeData(self, source: QMimeData):
        if source.hasText():
            text = source.text()
            if not _should_format_pasted_json(text):
                if _looks_like_json(text):
                    self._start_async_json_paste(text)
                else:
                    super().insertFromMimeData(source)
                return
            try:
                parsed = json.loads(text)
                if self._body_format == BodyFormat.YAML and self._yaml_as_json:
                    yaml_text = convert_json_object_to_yaml(parsed)
                    self.insertPlainText(yaml_text.rstrip("\n"))
                else:
                    formatted_json = json.dumps(parsed, indent=self.indent_size)
                    self.insertPlainText(formatted_json)
            except (json.JSONDecodeError, ValueError):
                super().insertFromMimeData(source)
        else:
            super().insertFromMimeData(source)

    def _start_async_json_paste(self, text: str) -> None:
        self._paste_json_generation += 1
        generation = self._paste_json_generation

        if self._paste_json_worker is not None and self._paste_json_worker.isRunning():
            self._paste_json_worker.requestInterruption()

        cursor = self.textCursor()
        self._async_paste_start = cursor.position()
        self._async_paste_original = text
        self.insertPlainText(text)
        self._async_paste_length = len(text)

        logger.debug(
            "code_editor_async_paste_started generation=%d chars=%d",
            generation,
            len(text),
        )

        worker = PasteJsonFormatWorker(
            generation,
            text,
            indent_size=self.indent_size,
            body_format=self._body_format,
            yaml_as_json=self._yaml_as_json,
        )
        worker.finished_with_result.connect(self._on_async_paste_formatted)
        worker.finished.connect(worker.deleteLater)
        self._paste_json_worker = worker
        worker.start()

    def _on_async_paste_formatted(self, generation: int, formatted: object) -> None:
        if generation != self._paste_json_generation:
            logger.debug(
                "code_editor_async_paste_skipped generation=%d reason=stale",
                generation,
            )
            return
        if not isinstance(formatted, str):
            logger.debug(
                "code_editor_async_paste_skipped generation=%d reason=not_json",
                generation,
            )
            return

        cursor = QTextCursor(self.document())
        cursor.setPosition(self._async_paste_start)
        cursor.setPosition(
            self._async_paste_start + self._async_paste_length,
            QTextCursor.MoveMode.KeepAnchor,
        )
        selected = cursor.selectedText().replace("\u2029", "\n")
        if selected != self._async_paste_original:
            logger.debug(
                "code_editor_async_paste_skipped generation=%d reason=edited",
                generation,
            )
            return

        cursor.insertText(formatted)
        logger.debug("code_editor_async_paste_applied generation=%d", generation)
