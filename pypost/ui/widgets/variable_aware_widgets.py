from __future__ import annotations

from typing import Dict, Optional, Set, Tuple

from PySide6.QtWidgets import QLineEdit, QPlainTextEdit, QTableWidget, QToolTip

from pypost.ui.widgets.mixins import (
    VariableHoverLocator,
    VariableHoverMixin,
    VariableHoverResolver,
)


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
        index = self.cursorPositionAt(event.position().toPoint())
        return text, index


class VariableAwarePlainTextEdit(VariableHoverMixin, QPlainTextEdit):
    """QPlainTextEdit with variable tooltip support."""

    def __init__(self, parent=None):
        QPlainTextEdit.__init__(self, parent)
        VariableHoverMixin.__init__(self)
        self._hover_line_scoped_scan = True

    def _get_text_at_cursor(self, event) -> Tuple[str, int]:
        cursor = self.cursorForPosition(event.position().toPoint())
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
        self._hover_cache_key: Optional[Tuple[int, int, str]] = None
        self._hover_cache_resolved: Optional[str] = None

    def set_variables(self, variables: Dict[str, str]):
        self._variables = variables
        self._clear_hover_cache()

    def set_hidden_keys(self, hidden_keys: Set[str]):
        self._hidden_keys = hidden_keys
        self._clear_hover_cache()

    def _clear_hover_cache(self) -> None:
        self._hover_cache_key = None
        self._hover_cache_resolved = None

    def _cell_hover_cache_key(self, item) -> Tuple[int, int, str]:
        return self.row(item), self.column(item), item.text()

    def _resolve_cell_hover(self, item) -> Optional[str]:
        """Resolve tooltip text for a cell; reuse cache on repeated moves (PYPOST-132)."""
        key = self._cell_hover_cache_key(item)
        if key == self._hover_cache_key:
            return self._hover_cache_resolved

        text = item.text()
        if not VariableHoverLocator.EXPRESSION_PATTERN.search(text):
            self._hover_cache_key = key
            self._hover_cache_resolved = None
            return None

        resolved = VariableHoverResolver.resolve_text(
            text,
            self._variables,
            self._hidden_keys,
        )
        self._hover_cache_key = key
        self._hover_cache_resolved = resolved
        return resolved

    def mouseMoveEvent(self, event):
        item = self.itemAt(event.position().toPoint())
        if item:
            resolved = self._resolve_cell_hover(item)
            if resolved is not None:
                QToolTip.showText(
                    event.globalPosition().toPoint(),
                    resolved,
                    self,
                )
            else:
                QToolTip.hideText()
        else:
            self._clear_hover_cache()
            QToolTip.hideText()

        super().mouseMoveEvent(event)
