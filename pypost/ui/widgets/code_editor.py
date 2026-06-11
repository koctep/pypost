import json

from PySide6.QtCore import QMimeData, Qt, QRect
from PySide6.QtGui import QFontMetrics, QKeyEvent, QPaintEvent, QPainter, QTextCursor
from PySide6.QtWidgets import QPlainTextEdit

from pypost.ui.widgets.line_number_area import LineNumberArea
from pypost.ui.widgets.variable_aware_widgets import VariableAwarePlainTextEdit


class CodeEditor(VariableAwarePlainTextEdit):
    def __init__(self, parent=None, indent_size=2):
        super().__init__(parent)
        self.indent_size = indent_size
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        self._line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self._update_line_number_area_width(0)

        self.update_indent_size(indent_size)

    def update_indent_size(self, new_size: int):
        self.indent_size = new_size
        # Set tab stop to indent_size spaces
        font = self.document().defaultFont()
        font_metrics = QFontMetrics(font)
        self.setTabStopDistance(self.indent_size * font_metrics.horizontalAdvance(" "))

    def line_number_area_width(self) -> int:
        digits = max(1, len(str(self.blockCount())))
        font_metrics = QFontMetrics(self.document().defaultFont())
        space = 3 + font_metrics.horizontalAdvance("9") * digits
        return space

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

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.drawText(
                    0,
                    top,
                    self._line_number_area.width() - 3,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    number,
                )

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
            pass  # Keep as is if not valid JSON

    def keyPressEvent(self, event: QKeyEvent):
        """
        Handle key press events for auto-indentation.
        """
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

        # Calculate current indentation
        indent = ""
        for char in line_text:
            if char.isspace():
                indent += char
            else:
                break

        # Check if line ends with opening bracket
        trimmed_line = line_text.rstrip()
        if trimmed_line and trimmed_line[-1] in ("{", "["):
            indent += " " * self.indent_size  # Add indent_size spaces

        # Insert new line with indentation
        self.insertPlainText("\n" + indent)

    def _handle_closing_bracket(self, event: QKeyEvent):
        cursor = self.textCursor()
        current_line_text = cursor.block().text()

        # Check if we are at the beginning of the line (ignoring whitespace)
        # to dedent only if it's the first non-whitespace char
        if current_line_text.strip() == "":
            # Calculate indentation of the previous line to match context if possible,
            # or simply unindent by 4 spaces if currently indented

            # Current approach: Dedent if the line consists only of indentation so far
            # and the user types '}' or ']'

            # Get current indentation level
            indent_level = len(current_line_text) - len(current_line_text.lstrip())

            if indent_level >= self.indent_size:
                # Remove indent_size spaces from the start
                cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
                cursor.movePosition(
                    QTextCursor.MoveOperation.Right,
                    QTextCursor.MoveMode.KeepAnchor,
                    self.indent_size,
                )
                if cursor.selectedText() == " " * self.indent_size:
                    cursor.removeSelectedText()

        super().keyPressEvent(event)

    def insertFromMimeData(self, source: QMimeData):
        """
        Handle paste events for JSON formatting.
        """
        if source.hasText():
            text = source.text()
            try:
                # Try to parse and format JSON
                parsed = json.loads(text)
                formatted_json = json.dumps(parsed, indent=self.indent_size)
                self.insertPlainText(formatted_json)
            except (json.JSONDecodeError, ValueError):
                # If not valid JSON, paste as is
                super().insertFromMimeData(source)
        else:
            super().insertFromMimeData(source)
