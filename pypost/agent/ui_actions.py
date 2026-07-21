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
    QComboBox,
    QLineEdit,
    QPlainTextEdit,
    QTextEdit,
    QWidget,
)

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


def ui_fill(root: QWidget, widget_id: str, text: str) -> None:
    """Replace the editable text of the named widget with ``text``."""
    started = time.monotonic()
    widget = find_widget(root, widget_id)
    _require_interactable(widget, widget_id)
    if isinstance(widget, QLineEdit):
        widget.clear()
        widget.setText(text)
    elif isinstance(widget, (QPlainTextEdit, QTextEdit)):
        widget.clear()
        widget.setPlainText(text)
    else:
        raise UiTargetNotInteractableError(
            widget_id,
            f"not a text input (type={type(widget).__name__})",
        )
    _pump()
    duration_ms = int((time.monotonic() - started) * 1000)
    logger.debug(
        "ui_action_applied primitive=fill widget_id=%s outcome=ok duration_ms=%s",
        widget_id,
        duration_ms,
    )


def ui_select(root: QWidget, widget_id: str, option: str) -> None:
    """Select ``option`` (display text) on a named combo box."""
    started = time.monotonic()
    widget = find_widget(root, widget_id)
    _require_interactable(widget, widget_id)
    if not isinstance(widget, QComboBox):
        raise UiTargetNotInteractableError(
            widget_id,
            f"not a combo box (type={type(widget).__name__})",
        )
    index = widget.findText(option)
    if index < 0:
        raise UiTargetNotInteractableError(
            widget_id,
            f"option not found: {option!r}",
        )
    widget.setCurrentIndex(index)
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
