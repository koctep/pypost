from typing import Dict, Set, Tuple
from PySide6.QtWidgets import (
    QLineEdit, QPlainTextEdit, QTableWidget, QToolTip,
)
from pypost.ui.widgets.mixins import VariableHoverMixin, VariableHoverHelper


class VariableAwareLineEdit(VariableHoverMixin, QLineEdit):
    """QLineEdit with variable tooltip support."""

    def __init__(self, parent=None):
        QLineEdit.__init__(self, parent)
        VariableHoverMixin.__init__(self)

    def _get_text_at_cursor(self, event) -> Tuple[str, int]:
        text = self.text()
        if not text:
            return "", 0

        # Calculate character index under cursor
        index = self.cursorPositionAt(event.pos())
        return text, index


class VariableAwarePlainTextEdit(VariableHoverMixin, QPlainTextEdit):
    """QPlainTextEdit with variable tooltip support."""

    def __init__(self, parent=None):
        QPlainTextEdit.__init__(self, parent)
        VariableHoverMixin.__init__(self)

    def _get_text_at_cursor(self, event) -> Tuple[str, int]:
        cursor = self.cursorForPosition(event.pos())
        text = self.toPlainText()
        index = cursor.position()
        return text, index


class VariableAwareTableWidget(QTableWidget):
    """QTableWidget with variable tooltip support."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMouseTracking(True)
        self._variables: Dict[str, str] = {}
        self._hidden_keys: Set[str] = set()

    def set_variables(self, variables: Dict[str, str]):
        self._variables = variables

    def set_hidden_keys(self, hidden_keys: Set[str]):
        self._hidden_keys = hidden_keys

    def mouseMoveEvent(self, event):
        item = self.itemAt(event.pos())
        if item:
            text = item.text()
            if VariableHoverHelper.EXPRESSION_PATTERN.search(text):
                resolved = VariableHoverHelper.resolve_text(
                    text, self._variables, self._hidden_keys,
                )
                QToolTip.showText(
                    event.globalPos(), resolved, self,
                )
            else:
                QToolTip.hideText()
        else:
            QToolTip.hideText()

        super().mouseMoveEvent(event)
