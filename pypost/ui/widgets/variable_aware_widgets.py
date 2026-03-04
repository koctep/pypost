from typing import Dict, Optional, Tuple
from PySide6.QtWidgets import QLineEdit, QPlainTextEdit, QTableWidget, QToolTip
from PySide6.QtCore import Qt
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
    """
    QTableWidget with variable tooltip support.
    Note: TableWidget structure is different (items vs text stream), so we override mouseMoveEvent manually
    or we could adapt the mixin. For now, let's keep the manual implementation but use the Helper.
    Or adapt to Mixin if possible. 
    Actually, TableWidget hovers over items, which is slightly different than text cursor position.
    Let's keep using VariableHoverHelper but implement mouseMoveEvent directly as before, 
    since mixin expects _get_text_at_cursor logic which applies to text fields.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMouseTracking(True)
        self._variables: Dict[str, str] = {}

    def set_variables(self, variables: Dict[str, str]):
        self._variables = variables

    def mouseMoveEvent(self, event):
        item = self.itemAt(event.pos())
        if item:
            text = item.text()
            # If text has variables, show resolved text tooltip
            if VariableHoverHelper.VARIABLE_PATTERN.search(text):
                resolved = VariableHoverHelper.resolve_text(text, self._variables)
                # Show tooltip with resolved content
                QToolTip.showText(event.globalPos(), resolved, self)
            else:
                QToolTip.hideText()
        else:
            QToolTip.hideText()
        
        super().mouseMoveEvent(event)
