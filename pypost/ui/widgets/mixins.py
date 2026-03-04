from typing import Dict, Optional, Tuple
from PySide6.QtWidgets import QToolTip, QWidget
from PySide6.QtCore import QPoint
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


class VariableHoverMixin:
    """
    Mixin for QWidgets to support hovering over {{variables}}.
    Requires the host class to be a QWidget subclass.
    """
    def __init__(self):
        self._variables: Dict[str, str] = {}
        # Ensure mouse tracking is enabled. 
        # Note: If mixin is initialized after super().__init__, this works.
        if isinstance(self, QWidget):
            self.setMouseTracking(True)

    def set_variables(self, variables: Dict[str, str]):
        self._variables = variables

    def _get_text_at_cursor(self, event) -> Tuple[str, int]:
        """
        Abstract method to get text and index at cursor position.
        Must be implemented by subclasses.
        Returns (full_text, cursor_index)
        """
        raise NotImplementedError("Subclasses must implement _get_text_at_cursor")

    def mouseMoveEvent(self, event):
        # Allow default processing first (e.g. selection)
        super().mouseMoveEvent(event) # type: ignore

        try:
            text, index = self._get_text_at_cursor(event)
        except NotImplementedError:
            return

        if not text:
            return

        # Check the variable at this index
        var_name = VariableHoverHelper.find_variable_at_index(text, index)
        # Check previous char if we are at the end of a variable
        if not var_name and index > 0:
             var_name = VariableHoverHelper.find_variable_at_index(text, index - 1)

        if var_name:
            value = VariableHoverHelper.get_variable_value(var_name, self._variables)
            # Show tooltip globally
            QToolTip.showText(event.globalPos(), value, self) # type: ignore
        else:
            QToolTip.hideText()

