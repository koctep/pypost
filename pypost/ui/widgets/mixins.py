from typing import Dict, Optional, Set, Tuple
from PySide6.QtWidgets import QToolTip, QWidget
import re
from pypost.core.template_service import TemplateService
from pypost.core.metrics import MetricsManager

HIDDEN_MASK = "********"


class VariableHoverHelper:
    """Helper class to find variables in text and manage tooltip display."""

    # Regex to find {{variable}} pattern
    VARIABLE_PATTERN = re.compile(r'\{\{([a-zA-Z0-9_]+)\}\}')
    EXPRESSION_PATTERN = re.compile(r"\{\{\s*([^{}]+?)\s*\}\}")
    _template_service = TemplateService()

    @classmethod
    def set_metrics(cls, metrics: MetricsManager | None) -> None:
        """
        Rebuild helper TemplateService so hover path exports observability metrics.
        """
        cls._template_service = TemplateService(metrics=metrics)

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
    def find_expression_at_index(text: str, index: int) -> Optional[str]:
        """
        Finds full `{{...}}` function placeholder token (e.g. {{urlencode(db)}}) under index.
        Returns full token with braces or None.
        """
        for match in VariableHoverHelper.EXPRESSION_PATTERN.finditer(text):
            if match.start() <= index < match.end():
                return match.group(0)
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
        """Replaces all supported {{...}} occurrences with hover values."""
        def replace(match):
            expression = match.group(0)
            if VariableHoverHelper.VARIABLE_PATTERN.fullmatch(expression):
                return VariableHoverHelper._resolve_plain_variable(
                    expression, variables, hidden_keys,
                )
            return VariableHoverHelper._resolve_expression_token(
                expression, variables,
            )
        return VariableHoverHelper.EXPRESSION_PATTERN.sub(replace, text)

    @staticmethod
    def _resolve_plain_variable(
        expression: str,
        variables: Dict[str, str],
        hidden_keys: Optional[Set[str]] = None,
    ) -> str:
        match = VariableHoverHelper.VARIABLE_PATTERN.fullmatch(expression)
        if not match:
            return expression
        return VariableHoverHelper.get_variable_value(
            match.group(1), variables, hidden_keys,
        )

    @staticmethod
    def _resolve_expression_token(expression: str, variables: Dict[str, str]) -> str:
        return VariableHoverHelper._template_service.render_string(
            expression, variables, render_path="hover",
        )


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

        expression = self._find_hover_expression(text, index)
        self._show_or_hide_tooltip(event, expression)

    def _find_hover_expression(self, text: str, index: int) -> Optional[str]:
        expression = VariableHoverHelper.find_expression_at_index(text, index)
        if expression or index <= 0:
            return expression
        return VariableHoverHelper.find_expression_at_index(text, index - 1)

    def _show_or_hide_tooltip(self, event, expression: Optional[str]) -> None:
        if not expression:
            QToolTip.hideText()
            return

        value = VariableHoverHelper.resolve_text(
            expression, self._variables, self._hidden_keys,
        )
        QToolTip.showText(
            event.globalPos(), value, self,  # type: ignore
        )
