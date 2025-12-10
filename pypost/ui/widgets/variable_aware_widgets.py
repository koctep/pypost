from typing import Optional, Dict
from PySide6.QtWidgets import QLineEdit, QPlainTextEdit, QToolTip
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
        # cursorPositionAt returns the nearest cursor position, 
        # but we need to check if the mouse is actually over the text rect
        # For simplicity, we assume if it's inside the widget and we get an index, it's valid-ish.
        # But cursorPositionAt returns the insertion point between characters.
        
        index = self.cursorPositionAt(pos)
        
        # Adjust index: cursorPositionAt returns index where caret would be. 
        # If we hover over char 'a' at index 0, it might return 0 or 1 depending on which half.
        # Let's try to map strictly.
        # Actually, QLineEdit doesn't expose strict char hit testing easily.
        # But checking around the index is usually enough for {{var}}.
        
        text = self.text()
        if not text:
            super().mouseMoveEvent(event)
            return

        # Check the variable at this index
        # We might need to check index and index-1 because cursorPositionAt is "between" chars.
        var_name = VariableHoverHelper.find_variable_at_index(text, index)
        if not var_name and index > 0:
             var_name = VariableHoverHelper.find_variable_at_index(text, index - 1)

        if var_name:
            value = VariableHoverHelper.get_variable_value(var_name, self._variables)
            # Show tooltip globally
            QToolTip.showText(event.globalPos(), f"{var_name}: {value}", self)
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
        # cursor.position() is the absolute position in document
        
        # Check if we are actually over the text block?
        # cursorForPosition returns the nearest cursor.
        
        text = self.toPlainText()
        index = cursor.position()
        
        var_name = VariableHoverHelper.find_variable_at_index(text, index)
        if not var_name and index > 0:
            var_name = VariableHoverHelper.find_variable_at_index(text, index - 1)

        if var_name:
            value = VariableHoverHelper.get_variable_value(var_name, self._variables)
            QToolTip.showText(event.globalPos(), f"{var_name}: {value}", self)
        else:
            QToolTip.hideText()
            
        super().mouseMoveEvent(event)

