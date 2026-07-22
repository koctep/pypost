"""Visible UI state snapshot for agents (PYPOST-835).

Walks the visible ``QWidget`` tree from ``MainWindow`` and returns a nested
dict of ``role`` / ``name`` / ``value`` / ``children``. String values are
sanitized with the active environment's variables and ``hidden_keys``.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QTreeView,
    QWidget,
)

from pypost.core.sensitive_text_sanitizer import sanitize_text

logger = logging.getLogger(__name__)

# Max characters kept in a single snapshot ``value`` (verification-sized).
UI_SNAPSHOT_MAX_VALUE_LENGTH = 500
# Max selected item-view cells summarized into ``value`` (multi-select cap).
UI_SNAPSHOT_ITEM_VIEW_SELECTION_CAP = 5

_ROLE_BY_TYPE: tuple[tuple[type, str], ...] = (
    (QMainWindow, "window"),
    (QLineEdit, "line_edit"),
    (QComboBox, "combo_box"),
    (QPushButton, "button"),
    (QLabel, "label"),
    (QTabWidget, "tab_widget"),
    (QTreeView, "tree_view"),
    (QAbstractItemView, "item_view"),
    (QPlainTextEdit, "text_edit"),
    (QTextEdit, "text_edit"),
)


def capture_ui_snapshot(window: QWidget) -> dict[str, Any]:
    """Return a structured visible-UI tree (roles, names, values, hierarchy).

    Sensitive substrings follow ``sensitive_text_sanitizer`` with the active
    environment variables and ``hidden_keys``. Caller should ensure
    ``is_ui_ready``.

    Logs a DEBUG summary (counts + duration) only — never the tree or values.
    """
    started = time.monotonic()
    env_vars, hidden_keys = _active_env_context(window)
    node = _build_node(window, env_vars=env_vars, hidden_keys=hidden_keys)
    if node is None:
        node = {
            "role": _role_for(window),
            "name": window.objectName() or "",
            "value": None,
            "children": [],
        }
    node_count, named_count = _count_nodes(node)
    duration_ms = int((time.monotonic() - started) * 1000)
    # Scalars only — never log tree, values, env_vars, or hidden_keys.
    logger.debug(
        "ui_snapshot_captured node_count=%s named_count=%s duration_ms=%s",
        node_count,
        named_count,
        duration_ms,
    )
    return node


def _count_nodes(node: dict[str, Any]) -> tuple[int, int]:
    """Return ``(total_nodes, named_nodes)`` for a snapshot tree."""
    total = 1
    named = 1 if node.get("name") else 0
    for child in node.get("children") or []:
        child_total, child_named = _count_nodes(child)
        total += child_total
        named += child_named
    return total, named


def _active_env_context(window: QWidget) -> tuple[dict[str, str], set[str]]:
    """Read active env vars / hidden_keys via EnvPresenter public accessors."""
    env = getattr(window, "env", None)
    if env is None:
        return {}, set()
    variables = getattr(env, "current_variables", None)
    env_vars = dict(variables) if isinstance(variables, dict) else {}
    hidden = getattr(env, "current_hidden_keys", None)
    hidden_keys = set(hidden) if isinstance(hidden, (set, frozenset)) else set()
    return env_vars, hidden_keys


def _role_for(widget: QWidget) -> str:
    for cls, role in _ROLE_BY_TYPE:
        if isinstance(widget, cls):
            return role
    return "widget"


def _raw_value(widget: QWidget) -> str | None:
    if isinstance(widget, QLineEdit):
        return widget.text()
    if isinstance(widget, QComboBox):
        return widget.currentText()
    if isinstance(widget, QPushButton):
        return widget.text()
    if isinstance(widget, QLabel):
        return widget.text()
    if isinstance(widget, QTabWidget):
        idx = widget.currentIndex()
        if idx < 0:
            return ""
        return widget.tabText(idx)
    if isinstance(widget, (QPlainTextEdit, QTextEdit)):
        return widget.toPlainText()
    if isinstance(widget, QAbstractItemView):
        indexes = widget.selectedIndexes()
        if not indexes:
            return ""
        model = widget.model()
        if model is None:
            return ""
        parts = [
            str(model.data(idx) or "")
            for idx in indexes[:UI_SNAPSHOT_ITEM_VIEW_SELECTION_CAP]
            if model.data(idx) is not None
        ]
        return ", ".join(p for p in parts if p)
    return None


def _sanitize_value(
    raw: str | None,
    *,
    env_vars: dict[str, str],
    hidden_keys: set[str],
) -> str | None:
    if raw is None:
        return None
    text = sanitize_text(raw, env_vars=env_vars, hidden_keys=hidden_keys)
    if len(text) > UI_SNAPSHOT_MAX_VALUE_LENGTH:
        return text[:UI_SNAPSHOT_MAX_VALUE_LENGTH]
    return text


def _iter_visible_child_widgets(widget: QWidget) -> list[QWidget]:
    children: list[QWidget] = []
    for child in widget.children():
        if isinstance(child, QWidget) and child.isVisible():
            children.append(child)
    return children


def _build_node(
    widget: QWidget,
    *,
    env_vars: dict[str, str],
    hidden_keys: set[str],
) -> dict[str, Any] | None:
    if not widget.isVisible():
        return None

    child_nodes: list[dict[str, Any]] = []
    for child in _iter_visible_child_widgets(widget):
        node = _build_node(child, env_vars=env_vars, hidden_keys=hidden_keys)
        if node is not None:
            child_nodes.append(node)

    name = widget.objectName() or ""
    value = _sanitize_value(
        _raw_value(widget),
        env_vars=env_vars,
        hidden_keys=hidden_keys,
    )

    # Prune unnamed chrome with no value and no kept descendants.
    if not name and value in (None, "") and not child_nodes:
        return None

    return {
        "role": _role_for(widget),
        "name": name,
        "value": value,
        "children": child_nodes,
    }
