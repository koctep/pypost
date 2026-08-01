"""UI action primitives for agents (PYPOST-836).

Resolve targets by stable ``objectName`` (widget ids), then click, fill, select,
or send a key/hotkey. Raises actionable errors when the target is missing or
not interactable.
"""

from __future__ import annotations

import logging
import time
from typing import Final

from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QLineEdit,
    QListWidget,
    QPlainTextEdit,
    QTextEdit,
    QTreeView,
    QWidget,
)

from pypost.agent.tree_index import find_tree_index_by_display_text

logger = logging.getLogger(__name__)

_KEY_ALIASES: Final[dict[str, Qt.Key]] = {
    "return": Qt.Key.Key_Return,
    "enter": Qt.Key.Key_Enter,
    "escape": Qt.Key.Key_Escape,
    "esc": Qt.Key.Key_Escape,
    "tab": Qt.Key.Key_Tab,
    "backspace": Qt.Key.Key_Backspace,
    "delete": Qt.Key.Key_Delete,
    "space": Qt.Key.Key_Space,
    "up": Qt.Key.Key_Up,
    "down": Qt.Key.Key_Down,
    "left": Qt.Key.Key_Left,
    "right": Qt.Key.Key_Right,
    "home": Qt.Key.Key_Home,
    "end": Qt.Key.Key_End,
}


class UiActionError(Exception):
    """Base error for agent UI action failures."""


class UiTargetNotFoundError(UiActionError):
    """No widget with the given widget id under the lookup root."""

    def __init__(self, widget_id: str) -> None:
        self.widget_id = widget_id
        super().__init__(f"UI target not found: widget_id={widget_id!r}")


class UiTargetNotInteractableError(UiActionError):
    """Widget exists but cannot receive the requested action."""

    def __init__(self, widget_id: str, reason: str) -> None:
        self.widget_id = widget_id
        self.reason = reason
        super().__init__(
            f"UI target not interactable: widget_id={widget_id!r} reason={reason}"
        )


def find_widget(root: QWidget, widget_id: str) -> QWidget:
    """Return the first ``QWidget`` under ``root`` with ``objectName == widget_id``.

    Raises:
        UiTargetNotFoundError: No matching widget under ``root``.
    """
    if root.objectName() == widget_id:
        return root
    widget = root.findChild(QWidget, widget_id)
    if widget is None:
        raise UiTargetNotFoundError(widget_id)
    return widget


def _require_interactable(widget: QWidget, widget_id: str) -> None:
    if not widget.isVisible():
        raise UiTargetNotInteractableError(widget_id, "not visible")
    if not widget.isEnabled():
        raise UiTargetNotInteractableError(widget_id, "not enabled")


def _pump() -> None:
    QCoreApplication.processEvents()


def _resolve_key(key: str) -> Qt.Key:
    normalized = key.strip().lower()
    if normalized in _KEY_ALIASES:
        return _KEY_ALIASES[normalized]
    if len(key) == 1:
        letter = key.upper()
        qt_key = getattr(Qt.Key, f"Key_{letter}", None)
        if qt_key is not None:
            return qt_key
    qt_key = getattr(Qt.Key, f"Key_{key}", None)
    if qt_key is not None:
        return qt_key
    raise ValueError(f"unsupported key name={key!r}")


def ui_click(root: QWidget, widget_id: str) -> None:
    """Left-click the named widget (must be visible and enabled)."""
    started = time.monotonic()
    widget = find_widget(root, widget_id)
    _require_interactable(widget, widget_id)
    QTest.mouseClick(widget, Qt.MouseButton.LeftButton)
    _pump()
    duration_ms = int((time.monotonic() - started) * 1000)
    logger.debug(
        "ui_action_applied primitive=click widget_id=%s outcome=ok duration_ms=%s",
        widget_id,
        duration_ms,
    )


def ui_fill(
    root: QWidget,
    widget_id: str,
    text: str,
    *,
    via_key_clicks: bool = False,
) -> None:
    """Replace the editable text of the named widget with ``text``.

    When ``via_key_clicks`` is True, clear and focus the field, then deliver
    ``text`` via ``QTest.keyClicks`` for keystroke-level realism.
    """
    started = time.monotonic()
    widget = find_widget(root, widget_id)
    _require_interactable(widget, widget_id)
    if not isinstance(widget, (QLineEdit, QPlainTextEdit, QTextEdit)):
        raise UiTargetNotInteractableError(
            widget_id,
            f"not a text input (type={type(widget).__name__})",
        )
    if via_key_clicks:
        widget.clear()
        widget.setFocus(Qt.FocusReason.OtherFocusReason)
        _pump()
        QTest.keyClicks(widget, text)
    elif isinstance(widget, QLineEdit):
        widget.clear()
        widget.setText(text)
    else:
        widget.clear()
        widget.setPlainText(text)
    _pump()
    duration_ms = int((time.monotonic() - started) * 1000)
    logger.debug(
        "ui_action_applied primitive=fill widget_id=%s outcome=ok "
        "duration_ms=%s via_key_clicks=%s",
        widget_id,
        duration_ms,
        str(via_key_clicks).lower(),
    )


def _select_combo(widget: QComboBox, widget_id: str, option: str | int) -> None:
    if isinstance(option, int):
        if option < 0 or option >= widget.count():
            raise UiTargetNotInteractableError(
                widget_id,
                f"option index out of range: {option!r}",
            )
        widget.setCurrentIndex(option)
        return
    index = widget.findText(option)
    if index < 0:
        raise UiTargetNotInteractableError(
            widget_id,
            f"option not found: {option!r}",
        )
    widget.setCurrentIndex(index)


def _select_list(widget: QListWidget, widget_id: str, option: str | int) -> None:
    if isinstance(option, int):
        if option < 0 or option >= widget.count():
            raise UiTargetNotInteractableError(
                widget_id,
                f"option index out of range: {option!r}",
            )
        widget.setCurrentRow(option)
        return
    matches = widget.findItems(option, Qt.MatchFlag.MatchExactly)
    if not matches:
        raise UiTargetNotInteractableError(
            widget_id,
            f"option not found: {option!r}",
        )
    widget.setCurrentItem(matches[0])


def _select_item_view(
    widget: QAbstractItemView,
    widget_id: str,
    option: str | int,
) -> None:
    model = widget.model()
    if model is None:
        raise UiTargetNotInteractableError(widget_id, "item view has no model")
    if isinstance(option, int):
        if option < 0 or option >= model.rowCount():
            raise UiTargetNotInteractableError(
                widget_id,
                f"option index out of range: {option!r}",
            )
        index = model.index(option, 0)
        if not index.isValid():
            raise UiTargetNotInteractableError(
                widget_id,
                f"option index out of range: {option!r}",
            )
        widget.setCurrentIndex(index)
        return
    rows = model.rowCount()
    for row in range(rows):
        index = model.index(row, 0)
        if not index.isValid():
            continue
        if str(index.data(Qt.ItemDataRole.DisplayRole)) == option:
            widget.setCurrentIndex(index)
            return
    raise UiTargetNotInteractableError(
        widget_id,
        f"option not found: {option!r}",
    )


def _select_tree(widget: QTreeView, widget_id: str, option: str | int) -> None:
    model = widget.model()
    if model is None:
        raise UiTargetNotInteractableError(widget_id, "tree has no model")
    if isinstance(option, int):
        if option < 0 or option >= model.rowCount():
            raise UiTargetNotInteractableError(
                widget_id,
                f"option index out of range: {option!r}",
            )
        index = model.index(option, 0)
        if not index.isValid():
            raise UiTargetNotInteractableError(
                widget_id,
                f"option index out of range: {option!r}",
            )
        widget.setCurrentIndex(index)
        return
    index = find_tree_index_by_display_text(widget, option)
    if index is None or not index.isValid():
        raise UiTargetNotInteractableError(
            widget_id,
            f"option not found: {option!r}",
        )
    parent = index.parent()
    if parent.isValid() and not widget.isExpanded(parent):
        widget.expand(parent)
        _pump()
    widget.setCurrentIndex(index)


def ui_select(root: QWidget, widget_id: str, option: str | int) -> None:
    """Select ``option`` by display text (str) or index (int).

    Supports ``QComboBox``, ``QListWidget``, ``QTreeView``, and flat
    model-backed ``QAbstractItemView`` targets (for example ``QListView``).
    For trees, an integer selects a top-level row; nested rows are selected
    by display text.
    """
    started = time.monotonic()
    widget = find_widget(root, widget_id)
    _require_interactable(widget, widget_id)
    if isinstance(widget, QComboBox):
        _select_combo(widget, widget_id, option)
    elif isinstance(widget, QListWidget):
        _select_list(widget, widget_id, option)
    elif isinstance(widget, QTreeView):
        _select_tree(widget, widget_id, option)
    elif isinstance(widget, QAbstractItemView):
        _select_item_view(widget, widget_id, option)
    else:
        raise UiTargetNotInteractableError(
            widget_id,
            f"not a selectable list/combo/tree (type={type(widget).__name__})",
        )
    _pump()
    duration_ms = int((time.monotonic() - started) * 1000)
    logger.debug(
        "ui_action_applied primitive=select widget_id=%s outcome=ok duration_ms=%s",
        widget_id,
        duration_ms,
    )


def ui_send_key(
    root: QWidget,
    widget_id: str,
    key: str,
    *,
    modifiers: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier,
) -> None:
    """Deliver a key (with optional modifiers) to the named widget."""
    started = time.monotonic()
    widget = find_widget(root, widget_id)
    _require_interactable(widget, widget_id)
    try:
        qt_key = _resolve_key(key)
    except ValueError as exc:
        raise UiTargetNotInteractableError(widget_id, str(exc)) from exc
    widget.setFocus(Qt.FocusReason.OtherFocusReason)
    _pump()
    QTest.keyClick(widget, qt_key, modifiers)
    _pump()
    duration_ms = int((time.monotonic() - started) * 1000)
    logger.debug(
        "ui_action_applied primitive=send_key widget_id=%s outcome=ok "
        "duration_ms=%s",
        widget_id,
        duration_ms,
    )
