from typing import Any, Dict, Generic, Iterable, Optional, Set, Tuple, TypeVar

from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QToolTip, QWidget

from pypost.core.constants import HIDDEN_MASK
from pypost.core.metrics_protocol import MetricsTrackerProtocol, resolve_metrics
from pypost.core.template_expression_tokenizer import (
    PLAIN_VARIABLE_PATTERN,
    TEMPLATE_PLACEHOLDER_PATTERN,
    extract_plain_variable_name,
    is_plain_variable_token,
)
from pypost.core.template_service import TemplateService

# Maximum plain {{name}} follow hops in hover tooltips (cycle-safe bound).
TOOLTIP_REFERENCE_MAX_DEPTH = 32

_hover_template_service = TemplateService()


class _HoverHelperMeta(type):
    """Metaclass so tests can patch ``VariableHoverHelper._template_service`` on the class."""

    @property
    def _template_service(cls) -> TemplateService:
        return _hover_template_service

    @_template_service.setter
    def _template_service(cls, value: TemplateService) -> None:
        global _hover_template_service
        _hover_template_service = value


def push_snapshot_to_widgets(
    widgets: Iterable[Any],
    method_name: str,
    value: Any,
) -> None:
    """Call ``method_name(value)`` on widgets that implement the method.

    Composite request-editor widgets use this to fan out environment variable and
    hidden-key snapshots. See doc/dev/variable_propagation.md.
    """
    for widget in widgets:
        method = getattr(widget, method_name, None)
        if callable(method):
            method(value)


class VariableHoverLocator:
    """Locate ``{{...}}`` tokens under a text cursor index (PYPOST-129)."""

    # Plain {{name}} fast path — shared with core template_expression_tokenizer (PYPOST-113).
    VARIABLE_PATTERN = PLAIN_VARIABLE_PATTERN
    # Full-token scan shared with core template_expression_tokenizer (PYPOST-536).
    EXPRESSION_PATTERN = TEMPLATE_PLACEHOLDER_PATTERN

    @staticmethod
    def find_variable_at_index(
        text: str,
        index: int,
    ) -> Optional[str]:
        """
        Finds a variable name under the given index in text.
        Returns the variable name (without braces) or None.
        """
        for match in VariableHoverLocator.VARIABLE_PATTERN.finditer(text):
            if match.start() <= index < match.end():
                return match.group(1)
        return None

    @staticmethod
    def find_expression_at_index(text: str, index: int) -> Optional[str]:
        """
        Finds full `{{...}}` function placeholder token (e.g. {{urlencode(db)}}) under index.
        Returns full token with braces or None.
        """
        for match in VariableHoverLocator.EXPRESSION_PATTERN.finditer(text):
            if match.start() <= index < match.end():
                return match.group(0)
        return None


class VariableHoverResolver:
    """Resolve ``{{...}}`` tokens to hover preview values (PYPOST-129)."""

    @classmethod
    def set_metrics(cls, metrics: MetricsTrackerProtocol | None) -> None:
        """
        Rebuild helper TemplateService so hover path exports observability metrics.
        """
        global _hover_template_service
        _hover_template_service = TemplateService(metrics=resolve_metrics(metrics))

    @classmethod
    def _template_service(cls) -> TemplateService:
        return _hover_template_service

    @staticmethod
    def get_variable_value(
        variable_name: str,
        variables: Dict[str, str],
        hidden_keys: Optional[Set[str]] = None,
    ) -> str:
        """Returns the value of the variable or a default message."""
        if hidden_keys and variable_name in hidden_keys:
            return HIDDEN_MASK
        return VariableHoverResolver._resolve_plain_reference_chain(
            variable_name,
            variables,
            hidden_keys,
        )

    @staticmethod
    def _resolve_plain_reference_chain(
        name: str,
        variables: Dict[str, str],
        hidden_keys: Optional[Set[str]] = None,
        *,
        visited: Optional[Set[str]] = None,
        depth: int = 0,
    ) -> str:
        """Follow plain ``{{name}}`` references with cycle and depth bounds (PYPOST-123)."""
        if hidden_keys and name in hidden_keys:
            return HIDDEN_MASK

        raw = variables.get(name, "<not defined>")
        if raw == "<not defined>":
            return raw

        if not is_plain_variable_token(raw):
            return raw

        inner_name = extract_plain_variable_name(raw)
        if inner_name is None:
            return raw

        seen = visited if visited is not None else set()
        if inner_name in seen:
            return raw

        if depth >= TOOLTIP_REFERENCE_MAX_DEPTH:
            return raw

        return VariableHoverResolver._resolve_plain_reference_chain(
            inner_name,
            variables,
            hidden_keys,
            visited=seen | {name},
            depth=depth + 1,
        )

    @staticmethod
    def resolve_text(
        text: str,
        variables: Dict[str, str],
        hidden_keys: Optional[Set[str]] = None,
    ) -> str:
        """Replaces all supported {{...}} occurrences with hover values."""

        def replace(match):
            expression = match.group(0)
            if is_plain_variable_token(expression):
                return VariableHoverResolver._resolve_plain_variable(
                    expression,
                    variables,
                    hidden_keys,
                )
            return VariableHoverResolver._resolve_expression_token(
                expression,
                variables,
            )

        return VariableHoverLocator.EXPRESSION_PATTERN.sub(replace, text)

    @staticmethod
    def _resolve_plain_variable(
        expression: str,
        variables: Dict[str, str],
        hidden_keys: Optional[Set[str]] = None,
    ) -> str:
        name = extract_plain_variable_name(expression)
        if name is None:
            return expression
        return VariableHoverResolver.get_variable_value(
            name,
            variables,
            hidden_keys,
        )

    @staticmethod
    def _resolve_expression_token(expression: str, variables: Dict[str, str]) -> str:
        return VariableHoverResolver._template_service().render_string(
            expression,
            variables,
            render_path="hover",
        )


class VariableHoverHelper(metaclass=_HoverHelperMeta):
    """Backward-compatible facade over locator and resolver (PYPOST-129)."""

    VARIABLE_PATTERN = VariableHoverLocator.VARIABLE_PATTERN
    EXPRESSION_PATTERN = VariableHoverLocator.EXPRESSION_PATTERN

    @classmethod
    def set_metrics(cls, metrics: MetricsTrackerProtocol | None) -> None:
        VariableHoverResolver.set_metrics(metrics)

    @staticmethod
    def find_variable_at_index(text: str, index: int) -> Optional[str]:
        return VariableHoverLocator.find_variable_at_index(text, index)

    @staticmethod
    def find_expression_at_index(text: str, index: int) -> Optional[str]:
        return VariableHoverLocator.find_expression_at_index(text, index)

    @staticmethod
    def get_variable_value(
        variable_name: str,
        variables: Dict[str, str],
        hidden_keys: Optional[Set[str]] = None,
    ) -> str:
        return VariableHoverResolver.get_variable_value(
            variable_name,
            variables,
            hidden_keys,
        )

    @staticmethod
    def resolve_text(
        text: str,
        variables: Dict[str, str],
        hidden_keys: Optional[Set[str]] = None,
    ) -> str:
        return VariableHoverResolver.resolve_text(text, variables, hidden_keys)


TWidget = TypeVar("TWidget", bound=QWidget)


class VariableHoverMixin(Generic[TWidget]):
    """
    Mixin for QWidgets to support hovering over {{variables}}.
    Requires the host class to be a QWidget subclass.
    """

    def __init__(self: TWidget) -> None:
        self._variables: Dict[str, str] = {}
        self._hidden_keys: Set[str] = set()
        self._hover_line_scoped_scan = False
        self._hover_scan_cache_key: Optional[Tuple[str, int]] = None
        self._hover_scan_cache_expression: Optional[str] = None
        self._hover_scan_cache_resolved: Optional[str] = None
        self.setMouseTracking(True)

    def set_variables(self, variables: Dict[str, str]) -> None:
        """Store the latest environment variable snapshot for hover resolution.

        Called by parent composites (e.g. RequestWidget) when the active environment
        changes. Widgets read this dict on demand during mouseMoveEvent; they do not
        subscribe to EnvPresenter signals directly. See doc/dev/variable_propagation.md.
        """
        self._variables = variables
        self._clear_hover_scan_cache()

    def set_hidden_keys(self, hidden_keys: Set[str]) -> None:
        self._hidden_keys = hidden_keys
        self._clear_hover_scan_cache()

    def _clear_hover_scan_cache(self: TWidget) -> None:
        self._hover_scan_cache_key = None
        self._hover_scan_cache_expression = None
        self._hover_scan_cache_resolved = None

    def _get_text_at_cursor(self: TWidget, event: QMouseEvent) -> Tuple[str, int]:
        """
        Abstract method to get text and index at cursor position.
        Must be implemented by subclasses.
        Returns (full_text, cursor_index)
        """
        raise NotImplementedError("Subclasses must implement _get_text_at_cursor")

    @staticmethod
    def _slice_line_at_index(text: str, index: int) -> Tuple[str, int]:
        """Return line text and index within line for a document-global cursor index."""
        if not text:
            return text, index
        index = min(max(index, 0), len(text))
        line_start = text.rfind("\n", 0, index) + 1
        line_end = text.find("\n", index)
        if line_end == -1:
            line_end = len(text)
        return text[line_start:line_end], index - line_start

    def _prepare_hover_scan_context(
        self: TWidget,
        text: str,
        index: int,
    ) -> Tuple[str, int]:
        """Narrow scan scope before expression lookup (line-only for multiline editors)."""
        if self._hover_line_scoped_scan:
            return self._slice_line_at_index(text, index)
        return text, index

    def mouseMoveEvent(self: TWidget, event: QMouseEvent) -> None:
        super().mouseMoveEvent(event)

        try:
            text, index = self._get_text_at_cursor(event)
        except NotImplementedError:
            return

        if not text:
            return

        scan_text, scan_index = self._prepare_hover_scan_context(text, index)
        expression, resolved = self._resolve_hover_at_scan_index(scan_text, scan_index)
        self._show_or_hide_tooltip(event, expression, resolved)

    def _find_hover_expression(self, text: str, index: int) -> Optional[str]:
        expression = VariableHoverLocator.find_expression_at_index(text, index)
        if expression or index <= 0:
            return expression
        return VariableHoverLocator.find_expression_at_index(text, index - 1)

    def _resolve_hover_at_scan_index(
        self: TWidget,
        scan_text: str,
        scan_index: int,
    ) -> Tuple[Optional[str], Optional[str]]:
        """Return (expression, resolved tooltip) for scan scope; reuse cache on repeat moves."""
        cache_key = (scan_text, scan_index)
        if cache_key == self._hover_scan_cache_key:
            return self._hover_scan_cache_expression, self._hover_scan_cache_resolved

        expression = self._find_hover_expression(scan_text, scan_index)
        resolved: Optional[str] = None
        if expression:
            resolved = VariableHoverResolver.resolve_text(
                expression,
                self._variables,
                self._hidden_keys,
            )

        self._hover_scan_cache_key = cache_key
        self._hover_scan_cache_expression = expression
        self._hover_scan_cache_resolved = resolved
        return expression, resolved

    def _show_or_hide_tooltip(
        self: TWidget,
        event: QMouseEvent,
        expression: Optional[str],
        resolved: Optional[str] = None,
    ) -> None:
        if not expression:
            QToolTip.hideText()
            return

        value = resolved
        if value is None:
            value = VariableHoverResolver.resolve_text(
                expression,
                self._variables,
                self._hidden_keys,
            )
        QToolTip.showText(
            event.globalPosition().toPoint(),
            value,
            self,
        )
