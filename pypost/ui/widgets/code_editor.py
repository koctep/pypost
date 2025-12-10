from PySide6.QtWidgets import QPlainTextEdit
from PySide6.QtGui import QKeyEvent, QFontMetrics, QTextCursor
from PySide6.QtCore import Qt, QMimeData
import json

class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None, indent_size=2):
        super().__init__(parent)
        self.indent_size = indent_size
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        
        self.update_indent_size(indent_size)

    def update_indent_size(self, new_size: int):
        self.indent_size = new_size
        # Set tab stop to indent_size spaces
        font = self.document().defaultFont()
        font_metrics = QFontMetrics(font)
        self.setTabStopDistance(self.indent_size * font_metrics.horizontalAdvance(' '))

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
            pass # Keep as is if not valid JSON

    def keyPressEvent(self, event: QKeyEvent):
        """
        Handle key press events for auto-indentation.
        """
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._handle_enter_key(event)
        elif event.text() in ('}', ']'):
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
        if trimmed_line and trimmed_line[-1] in ('{', '['):
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
                cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, self.indent_size)
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
