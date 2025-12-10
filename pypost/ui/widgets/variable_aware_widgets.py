from typing import Optional, Dict
from PySide6.QtWidgets import QLineEdit, QPlainTextEdit, QToolTip, QTableWidget
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QTextCursor
import re

class VariableHoverHelper:
    """Helper class to find variables in text and manage tooltip display."""
    
    # Regex to find {{variable}} pattern
    VARIABLE_PATTERN = re.compile(r'\{\{([a-zA-Z0-9_]+)\}\}')

    @staticmethod
    def find_variable_at_index(text: str, index: int) -> Optional[str]:
        """
        Finds a variable name under the given index in text.
        Returns the variable name (without braces) or None.
        """
        for match in VariableHoverHelper.VARIABLE_PATTERN.finditer(text):
            if match.start() <= index < match.end():
                return match.group(1)
        return None

    @staticmethod
    def get_variable_value(variable_name: str, variables: Dict[str, str]) -> str:
        """Returns the value of the variable or a default message."""
        return variables.get(variable_name, "<not defined>")

    @staticmethod
    def resolve_text(text: str, variables: Dict[str, str]) -> str:
        """Replaces all {{variable}} occurrences with their values."""
        def replace(match):
            var_name = match.group(1)
            # We want to show the value in the tooltip, so we return the value.
            return VariableHoverHelper.get_variable_value(var_name, variables)
        return VariableHoverHelper.VARIABLE_PATTERN.sub(replace, text)

class VariableAwareLineEdit(QLineEdit):
    """QLineEdit with variable tooltip support."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self._variables: Dict[str, str] = {}

    def set_variables(self, variables: Dict[str, str]):
        self._variables = variables

    def mouseMoveEvent(self, event):
        # Calculate character index under cursor
        pos = event.pos()
        # Ensure we are over text
        
        index = self.cursorPositionAt(pos)
        
        text = self.text()
        if not text:
            super().mouseMoveEvent(event)
            return

        # Check the variable at this index
        var_name = VariableHoverHelper.find_variable_at_index(text, index)
        if not var_name and index > 0:
             var_name = VariableHoverHelper.find_variable_at_index(text, index - 1)

        if var_name:
            value = VariableHoverHelper.get_variable_value(var_name, self._variables)
            # Show tooltip globally
            QToolTip.showText(event.globalPos(), value, self)
        else:
            QToolTip.hideText()
            
        super().mouseMoveEvent(event)

class VariableAwarePlainTextEdit(QPlainTextEdit):
    """QPlainTextEdit with variable tooltip support."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self._variables: Dict[str, str] = {}

    def set_variables(self, variables: Dict[str, str]):
        self._variables = variables

    def mouseMoveEvent(self, event):
        cursor = self.cursorForPosition(event.pos())
        
        text = self.toPlainText()
        index = cursor.position()
        
        var_name = VariableHoverHelper.find_variable_at_index(text, index)
        if not var_name and index > 0:
            var_name = VariableHoverHelper.find_variable_at_index(text, index - 1)

        if var_name:
            value = VariableHoverHelper.get_variable_value(var_name, self._variables)
            QToolTip.showText(event.globalPos(), value, self)
        else:
            QToolTip.hideText()
            
        super().mouseMoveEvent(event)

class VariableAwareTableWidget(QTableWidget):
    """QTableWidget with variable tooltip support."""

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
