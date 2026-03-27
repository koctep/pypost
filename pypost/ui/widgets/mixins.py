from typing import Dict, Optional, Set, Tuple
from PySide6.QtWidgets import QToolTip, QWidget
import re

HIDDEN_MASK = "********"


class VariableHoverHelper:
    """Helper class to find variables in text and manage tooltip display."""

    # Regex to find {{variable}} pattern
    VARIABLE_PATTERN = re.compile(r'\{\{([a-zA-Z0-9_]+)\}\}')

    @staticmethod
    def find_variable_at_index(
        text: str, index: int,
    ) -> Optional[str]:
        """
        Finds a variable name under the given index in text.
        Returns the variable name (without braces) or None.
        """
        for match in VariableHoverHelper.VARIABLE_PATTERN.finditer(text):
            if match.start() <= index < match.end():
                return match.group(1)
        return None

    @staticmethod
    def get_variable_value(
        variable_name: str,
        variables: Dict[str, str],
        hidden_keys: Optional[Set[str]] = None,
    ) -> str:
        """Returns the value of the variable or a default message."""
        if hidden_keys and variable_name in hidden_keys:
            return HIDDEN_MASK
        return variables.get(variable_name, "<not defined>")

    @staticmethod
    def resolve_text(
        text: str,
        variables: Dict[str, str],
        hidden_keys: Optional[Set[str]] = None,
    ) -> str:
        """Replaces all {{variable}} occurrences with their values."""
        def replace(match):
            var_name = match.group(1)
            return VariableHoverHelper.get_variable_value(
                var_name, variables, hidden_keys,
            )
        return VariableHoverHelper.VARIABLE_PATTERN.sub(replace, text)


class VariableHoverMixin:
    """
    Mixin for QWidgets to support hovering over {{variables}}.
    Requires the host class to be a QWidget subclass.
    """
    def __init__(self):
        self._variables: Dict[str, str] = {}
        self._hidden_keys: Set[str] = set()
        if isinstance(self, QWidget):
            self.setMouseTracking(True)

    def set_variables(self, variables: Dict[str, str]):
        self._variables = variables

    def set_hidden_keys(self, hidden_keys: Set[str]):
        self._hidden_keys = hidden_keys

    def _get_text_at_cursor(self, event) -> Tuple[str, int]:
        """
        Abstract method to get text and index at cursor position.
        Must be implemented by subclasses.
        Returns (full_text, cursor_index)
        """
        raise NotImplementedError(
            "Subclasses must implement _get_text_at_cursor"
        )

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)  # type: ignore

        try:
            text, index = self._get_text_at_cursor(event)
        except NotImplementedError:
            return

        if not text:
            return

        var_name = VariableHoverHelper.find_variable_at_index(
            text, index,
        )
        if not var_name and index > 0:
            var_name = VariableHoverHelper.find_variable_at_index(
                text, index - 1,
            )

        if var_name:
            value = VariableHoverHelper.get_variable_value(
                var_name, self._variables, self._hidden_keys,
            )
            QToolTip.showText(
                event.globalPos(), value, self,  # type: ignore
            )
        else:
            QToolTip.hideText()
