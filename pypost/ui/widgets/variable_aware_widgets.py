from __future__ import annotations

import logging
import re
from typing import Dict, Optional, Set, Tuple

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QLineEdit, QPlainTextEdit, QTableWidget, QTextEdit, QToolTip

from pypost.ui.widgets.variable_autocomplete_line_edit import reference_statuses
from pypost.ui.widgets.mixins import (
    VariableHoverLocator,
    VariableHoverMixin,
    VariableHoverResolver,
)

logger = logging.getLogger(__name__)


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

    def set_variables(self, variables: Dict[str, str]) -> None:
        self._variables = dict(variables)
        self._clear_hover_scan_cache()
        if hasattr(self, "refresh_reference_status"):
            self.refresh_reference_status(self.toPlainText())

    def set_hidden_keys(self, hidden_keys: Set[str]) -> None:
        self._hidden_keys = set(hidden_keys)
        self._clear_hover_scan_cache()

    def _track_reference_feedback(self, statuses) -> None:
        status_names: set[str] = set(str(status["kind"]) for status in statuses)
        if not status_names:
            status_names.add("ok")
        metrics = getattr(self, "_autocomplete_metrics", None)
        if metrics is not None:
            for status in status_names:
                metrics.track_gui_variable_autocomplete_feedback(
                    getattr(self, "_autocomplete_context", "unknown"), status
                )
        logger.debug(
            "variable_autocomplete_feedback context=%s statuses=%s",
            getattr(self, "_autocomplete_context", "unknown"),
            ",".join(sorted(status_names)),
        )


class VariableAwareTextEdit(VariableHoverMixin, QTextEdit):
    """QTextEdit with variable tooltip support."""

    def __init__(self, parent=None):
        QTextEdit.__init__(self, parent)
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
        self.itemChanged.connect(self._refresh_changed_item_feedback)

    def _refresh_changed_item_feedback(self, item) -> None:
        if item.column() == 1:
            self.refresh_reference_status(item.text())

    def set_variables(self, variables: Dict[str, str]):
        self._variables = variables
        self._clear_hover_cache()
        delegate = self.itemDelegateForColumn(1)
        if hasattr(delegate, "set_variables"):
            delegate.set_variables(variables)
        if hasattr(self, "refresh_reference_status"):
            for row in range(self.rowCount()):
                item = self.item(row, 1)
                if item:
                    self.refresh_reference_status(item.text())

    @property
    def environment_variable_names(self) -> list[str]:
        return sorted(self._variables)

    def complete_at_cursor(self, text: str, cursor_offset: int):
        prefix = text[:cursor_offset]
        match = re.search(r"\{\{\s*[A-Za-z0-9_]*$", prefix)
        if not match:
            return None
        token = re.sub(r"^\{\{\s*", "", prefix[match.start():]).lower()
        candidate = next(
            (name for name in self.environment_variable_names
             if name.lower().startswith(token)),
            None,
        )
        if candidate is None:
            return None
        start = match.start()
        return start, cursor_offset, f"{{{{ {candidate} }}}}"

    def show_reference_feedback(self, statuses) -> None:
        self._reference_feedback = list(statuses)

    def refresh_reference_status(self, text: str) -> None:
        statuses = reference_statuses(text, self._variables)
        self.show_reference_feedback(statuses)
        status_names: set[str] = set(str(status["kind"]) for status in statuses)
        if not status_names:
            status_names.add("ok")
        metrics = getattr(self, "_autocomplete_metrics", None)
        if metrics is not None:
            for status in status_names:
                metrics.track_gui_variable_autocomplete_feedback(
                    getattr(self, "_autocomplete_context", "unknown"), status
                )
        logger.debug(
            "variable_autocomplete_feedback context=%s statuses=%s",
            getattr(self, "_autocomplete_context", "unknown"),
            ",".join(sorted(status_names)),
        )
        message = "\n".join(status["message"] for status in statuses)
        for row in range(self.rowCount()):
            item = self.item(row, 1)
            if item and item.text() == text:
                item.setToolTip(message)
                item.setData(
                    Qt.ItemDataRole.ForegroundRole,
                    QColor("#b00020") if statuses else None,
                )

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
