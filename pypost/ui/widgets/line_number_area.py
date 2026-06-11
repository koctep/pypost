from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QKeyEvent, QMouseEvent, QPaintEvent
from PySide6.QtWidgets import QPlainTextEdit, QWidget


class LineNumberArea(QWidget):
    """Read-only gutter widget; painting is delegated to the host editor."""

    def __init__(self, editor: QPlainTextEdit):
        super().__init__(editor)
        self._editor = editor
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def sizeHint(self) -> QSize:
        return QSize(self._editor.line_number_area_width(), 0)

    def paintEvent(self, event: QPaintEvent):
        self._editor.line_number_area_paint_event(event)

    def mousePressEvent(self, event: QMouseEvent):
        self._editor.line_number_area_mouse_press(event)
        event.accept()

    def keyPressEvent(self, event: QKeyEvent):
        event.accept()
