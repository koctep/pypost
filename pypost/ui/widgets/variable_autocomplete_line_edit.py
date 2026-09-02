"""Reusable, name-only variable reference completion for request editors."""

from __future__ import annotations

import logging
import re
from typing import cast, Iterable, Literal, Protocol, Sequence, TypedDict

from PySide6.QtCore import QAbstractItemModel, QModelIndex, QPersistentModelIndex, Qt
from PySide6.QtGui import QFocusEvent, QHideEvent, QKeyEvent
from PySide6.QtWidgets import (
    QListWidget,
    QListWidgetItem,
    QLineEdit,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QWidget,
)
from pypost.core.metrics_protocol import MetricsTrackerProtocol, resolve_metrics

logger = logging.getLogger(__name__)
_legacy_logger = logging.getLogger("pypost.ui.widgets.mcp_server_headers_table")


class VariableNameProvider(Protocol):
    def variable_names(self) -> Sequence[str]: ...


class VariableReferenceStatus(TypedDict):
    kind: Literal["empty", "incomplete", "unavailable"]
    span: tuple[int, int]
    message: str


def reference_statuses(text: str, names: Iterable[str]) -> list[VariableReferenceStatus]:
    """Classify malformed or unavailable references without resolving their values."""
    known = set(names)
    statuses: list[VariableReferenceStatus] = []
    complete_end = 0
    for match in re.finditer(r"\{\{([^{}]*)\}\}", text):
        content = match.group(1).strip()
        if not content:
            statuses.append({"kind": "empty", "span": match.span(),
                             "message": "Variable name is missing."})
        elif content not in known:
            statuses.append({"kind": "unavailable", "span": match.span(),
                             "message": f"Variable '{content}' is unavailable."})
        complete_end = match.end()
    for opening in re.finditer(r"\{\{", text):
        next_open = text.find("{{", opening.end())
        next_close = text.find("}}", opening.end())
        if next_close < 0 or (next_open >= 0 and next_open < next_close):
            if opening.start() >= complete_end or next_open >= 0:
                statuses.append({"kind": "incomplete", "span": (opening.start(),
                                 next_open if next_open >= 0 else len(text)),
                                 "message": "Variable reference is unfinished."})
            break
    return statuses


class VariableAutocompleteLineEdit(QLineEdit):
    """Line editor that completes ``{{ NAME }}`` references without values."""

    def __init__(
        self,
        variables: Iterable[str] | None = None,
        parent: QWidget | None = None,
        *,
        metrics: MetricsTrackerProtocol | None = None,
        context: str = "query",
    ):
        super().__init__(parent)
        self._variables = list(variables or [])
        self._metrics = resolve_metrics(metrics)
        self._context = context
        self._popup = QListWidget(self)
        self._popup.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self._popup.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._popup.itemClicked.connect(self._on_item_clicked)
        self.textEdited.connect(lambda _text: self.trigger_autocomplete())

    def set_variables(self, variables: Iterable[str]) -> None:
        self._variables = list(variables)

    def is_popup_visible(self) -> bool:
        return self._popup.isVisible()

    def current_candidates(self) -> list[str]:
        return [self._popup.item(i).text() for i in range(self._popup.count())]

    def dismiss_popup(self) -> None:
        self._popup.hide()

    def _reference_match(self) -> re.Match[str] | None:
        before = self.text()[: self.cursorPosition()]
        return re.search(r"\{\{\s*([A-Za-z0-9_]*)$", before) or re.search(
            r"\{\{\s*([A-Za-z0-9_]*)(?:\s*\}\})?", self.text()
        )

    def _update_popup(self, candidates: list[str]) -> None:
        self._popup.clear()
        if not candidates:
            self.dismiss_popup()
            return
        self._popup.addItems(candidates)
        self._popup.setCurrentRow(0)
        if self.isVisible():
            self._popup.move(self.mapToGlobal(self.rect().bottomLeft()))
            self._popup.resize(max(self.width(), 180), min(160, 24 * len(candidates) + 8))
        self._popup.show()

    def trigger_autocomplete(self) -> None:
        match = self._reference_match()
        if match is None:
            self.dismiss_popup()
            return
        token = match.group(1)
        candidates = [
            name for name in self._variables if name.upper().startswith(token.upper())
        ]
        logger.debug(
            "variable_autocomplete_triggered context=%s candidates=%d",
            self._context,
            len(candidates),
        )
        _legacy_logger.debug(
            "Autocomplete triggered: prefix=%s, matched %d candidate(s) "
            "event=variable_autocomplete_triggered context=%s",
            token,
            len(candidates),
            self._context,
        )
        self._metrics.track_gui_variable_autocomplete_trigger(self._context)
        self._update_popup(candidates)

    def apply_completion(self, candidate: str) -> None:
        logger.info("variable_autocomplete_selected context=%s", self._context)
        _legacy_logger.info(
            "Autocomplete selected variable: %s event=variable_autocomplete_selected "
            "context=%s",
            candidate,
            self._context,
        )
        self._metrics.track_gui_variable_autocomplete_selection(self._context)
        match = self._reference_match()
        if match is None:
            self.insert(f"{{{{ {candidate} }}}}")
        else:
            start = match.start()
            end = self.cursorPosition()
            suffix = self.text()[end:]
            closing = re.match(r"^\s*\}\}", suffix)
            if closing:
                end += closing.end()
            replacement = f"{{{{ {candidate} }}}}"
            self.setText(self.text()[:start] + replacement + self.text()[end:])
            self.setCursorPosition(start + len(replacement))
        self.dismiss_popup()

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        self.apply_completion(item.text())

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if self.is_popup_visible():
            key = event.key()
            if key in (Qt.Key.Key_Down, Qt.Key.Key_Up):
                count = self._popup.count()
                if count:
                    delta = 1 if key == Qt.Key.Key_Down else -1
                    self._popup.setCurrentRow((self._popup.currentRow() + delta) % count)
                event.accept()
                return
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Tab):
                item = self._popup.currentItem() or self._popup.item(0)
                if item:
                    self.apply_completion(item.text())
                    event.accept()
                    return
            if key == Qt.Key.Key_Escape:
                self.dismiss_popup()
                event.accept()
                return
        super().keyPressEvent(event)

    def focusOutEvent(self, event: QFocusEvent) -> None:
        self.dismiss_popup()
        super().focusOutEvent(event)

    def hideEvent(self, event: QHideEvent) -> None:
        self.dismiss_popup()
        super().hideEvent(event)


class VariableAutocompleteDelegate(QStyledItemDelegate):
    """Delegate that supplies the shared editor for configured value columns."""

    def __init__(
        self,
        parent: QWidget | None = None,
        value_columns: Sequence[int] = (1,),
        *,
        metrics: MetricsTrackerProtocol | None = None,
        context: str = "query",
    ):
        super().__init__(parent)
        self._value_columns = set(value_columns)
        self._metrics = resolve_metrics(metrics)
        self._context = context
        self._editors: list[VariableAutocompleteLineEdit] = []

    def _names(self) -> Sequence[str]:
        provider = self.parent()
        if provider is not None and hasattr(provider, "environment_variable_names"):
            return cast(Sequence[str], provider.environment_variable_names)
        if provider is not None and hasattr(provider, "variable_names"):
            return cast(Sequence[str], provider.variable_names())
        return ()

    def createEditor(self, parent: QWidget | None, option: QStyleOptionViewItem,
                     index: QModelIndex | QPersistentModelIndex) -> QWidget:
        if index.column() in self._value_columns:
            editor = VariableAutocompleteLineEdit(
                self._names(), parent, metrics=self._metrics, context=self._context
            )
            self._editors.append(editor)
            editor.destroyed.connect(lambda _obj=None, item=editor: self._forget_editor(item))
            return editor
        return super().createEditor(parent, option, index)

    def _forget_editor(self, editor: VariableAutocompleteLineEdit) -> None:
        if editor in self._editors:
            self._editors.remove(editor)

    def set_variables(self, variables: Iterable[str]) -> None:
        """Refresh both future and currently open cell editors."""
        names = list(variables)
        self._metrics.track_gui_variable_autocomplete_environment_refresh(self._context)
        for editor in list(self._editors):
            editor.set_variables(names)
            editor.trigger_autocomplete()

    def setEditorData(self, editor: QWidget, index: QModelIndex | QPersistentModelIndex) -> None:
        if isinstance(editor, VariableAutocompleteLineEdit):
            editor.setText(str(index.data(Qt.ItemDataRole.EditRole) or ""))
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor: QWidget, model: QAbstractItemModel,
                     index: QModelIndex | QPersistentModelIndex) -> None:
        if isinstance(editor, VariableAutocompleteLineEdit):
            model.setData(index, editor.text(), Qt.ItemDataRole.EditRole)
        else:
            super().setModelData(editor, model, index)

    def updateEditorGeometry(self, editor: QWidget, option: QStyleOptionViewItem,
                             index: QModelIndex | QPersistentModelIndex) -> None:
        editor.setGeometry(option.rect)
