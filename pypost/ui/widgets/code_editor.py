import json

from PySide6.QtCore import QMimeData, Qt, QRect
from PySide6.QtGui import (
    QFontMetrics,
    QKeyEvent,
    QMouseEvent,
    QPaintEvent,
    QPainter,
    QTextCursor,
)
from PySide6.QtWidgets import QPlainTextEdit

from pypost.core.yaml_json_converter import convert_json_object_to_yaml
from pypost.ui.widgets.fold import BodyFormat, FoldController
from pypost.ui.widgets.line_number_area import LineNumberArea
from pypost.ui.widgets.validate import ValidationController
from pypost.ui.widgets.variable_aware_widgets import VariableAwarePlainTextEdit

_CHEVRON_WIDTH = 14
_CHEVRON_PADDING = 2


class CodeEditor(VariableAwarePlainTextEdit):
    def __init__(self, parent=None, indent_size=2):
        super().__init__(parent)
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

    def fold_controller(self) -> FoldController:
        return self._fold_controller

    def validation_controller(self) -> ValidationController:
        return self._validation_controller

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

    def update_indent_size(self, new_size: int):
        self.indent_size = new_size
        font = self.document().defaultFont()
        font_metrics = QFontMetrics(font)
        self.setTabStopDistance(self.indent_size * font_metrics.horizontalAdvance(" "))

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
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._handle_enter_key(event)
        elif event.text() in ("}", "]"):
            self._handle_closing_bracket(event)
        else:
            super().keyPressEvent(event)

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
