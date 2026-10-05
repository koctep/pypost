"""Register application hotkeys and collect them for the help dialog."""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable, Sequence

from PySide6.QtCore import SIGNAL
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import QWidget

logger = logging.getLogger(__name__)

SECTION_PROPERTY = "pypost_hotkey_section"
ORDER_PROPERTY = "pypost_hotkey_order"
ALT_KEYS_PROPERTY = "pypost_hotkey_alt_keys"
COLLAPSE_PROPERTY = "pypost_hotkey_collapse_keys"
LABEL_PROPERTY = "pypost_hotkey_label"

SECTION_ORDER = (
    "General",
    "Tabs",
    "Request Editor",
    "WebSocket Session",
    "MCP Client",
)


def format_shortcut_display(keys: Sequence[str], *, collapse: bool = False) -> str:
    if not keys:
        return ""
    if collapse and len(keys) > 2:
        return f"{keys[0]} ... {keys[-1]}"
    return " / ".join(keys)


def _keys_from_action(action: QAction) -> list[str]:
    alt = action.property(ALT_KEYS_PROPERTY)
    if alt and action.shortcut().isEmpty():
        return list(alt)
    keys: list[str] = []
    primary = action.shortcut().toString(QKeySequence.SequenceFormat.NativeText)
    if primary:
        keys.append(primary)
    if alt:
        keys.extend(alt)
    return keys


def collect_hotkey_rows(root: QWidget) -> list[tuple[str, str]]:
    """Return (label, shortcut) rows including section headers."""
    by_section: dict[str, list[tuple[int, str, str]]] = defaultdict(list)
    for action in root.findChildren(QAction):
        section = action.property(SECTION_PROPERTY)
        if not section:
            continue
        order = action.property(ORDER_PROPERTY)
        if order is None:
            order = 0
        display = action.property(LABEL_PROPERTY)
        label = str(display) if display else action.text().replace("&", "")
        keys = _keys_from_action(action)
        collapse = bool(action.property(COLLAPSE_PROPERTY))
        display = format_shortcut_display(keys, collapse=collapse)
        by_section[str(section)].append((int(order), label, display))

    rows: list[tuple[str, str]] = []
    seen_sections: set[str] = set()
    for section in SECTION_ORDER:
        if section not in by_section:
            continue
        rows.append((section, ""))
        for _, label, display in sorted(by_section[section], key=lambda item: item[0]):
            rows.append((label, display))
        seen_sections.add(section)
    for section in sorted(set(by_section) - seen_sections):
        rows.append((section, ""))
        for _, label, display in sorted(by_section[section], key=lambda item: item[0]):
            rows.append((label, display))
    return rows


def tag_action(
    action: QAction,
    *,
    section: str,
    order: int,
    keys: tuple[str, ...] | None = None,
    collapse_keys: bool = False,
    label: str | None = None,
) -> None:
    """Mark an existing QAction for hotkey help collection."""
    action.setProperty(SECTION_PROPERTY, section)
    action.setProperty(ORDER_PROPERTY, order)
    if label:
        action.setProperty(LABEL_PROPERTY, label)
    if keys:
        primary = action.shortcut().toString(QKeySequence.SequenceFormat.NativeText)
        if not primary:
            action.setShortcut(QKeySequence(keys[0]))
            extra = keys[1:]
        else:
            extra = [key for key in keys if key != primary]
        if extra:
            action.setProperty(ALT_KEYS_PROPERTY, list(extra))
    if collapse_keys:
        action.setProperty(COLLAPSE_PROPERTY, True)


def register_hotkey_documentation(
    parent: QWidget,
    *,
    section: str,
    label: str,
    keys: tuple[str, ...],
    order: int,
    collapse_keys: bool = False,
) -> QAction:
    """Register a display-only help-dialog row.

    The action never receives a ``QKeySequence``: every key is stored as
    platform-native text in ``ALT_KEYS_PROPERTY``, so a documentation row can
    never make a real binding with the same key ambiguous.
    """
    action = QAction(label, parent)
    tag_action(
        action,
        section=section,
        order=order,
        collapse_keys=collapse_keys,
        label=label,
    )
    native = QKeySequence.SequenceFormat.NativeText
    action.setProperty(
        ALT_KEYS_PROPERTY, [QKeySequence(key).toString(native) for key in keys]
    )
    parent.addAction(action)
    return action


def _on_shortcut_ambiguous(key: str) -> None:
    """Log a warning when Qt detects an ambiguous shortcut activation."""
    logger.warning("hotkey_ambiguous key=%s", key)


def register_hotkey(
    parent: QWidget,
    *,
    section: str,
    label: str,
    keys: tuple[str, ...],
    slot: Callable[[], None],
    order: int,
    collapse_keys: bool = False,
) -> QAction:
    """Create a QAction with one or more shortcut bindings."""
    action = QAction(label, parent)
    if keys:
        action.setShortcut(QKeySequence(keys[0]))
    action.triggered.connect(slot)
    tag_action(
        action,
        section=section,
        order=order,
        keys=keys,
        collapse_keys=collapse_keys,
    )
    parent.addAction(action)
    for alt_key in keys[1:]:
        shortcut = QShortcut(QKeySequence(alt_key), parent)
        shortcut.activated.connect(slot)
        shortcut.activatedAmbiguously.connect(
            lambda k=alt_key: _on_shortcut_ambiguous(k)
        )
    return action


def register_hotkey_group(
    parent: QWidget,
    *,
    section: str,
    label: str,
    bindings: tuple[tuple[str, Callable[[], None]], ...],
    order: int,
    collapse_keys: bool = True,
) -> QAction:
    """One help row with independent shortcut bindings (e.g. Alt+1..Alt+9)."""
    keys = tuple(key for key, _ in bindings)
    action = QAction(label, parent)
    action.setProperty(SECTION_PROPERTY, section)
    action.setProperty(ORDER_PROPERTY, order)
    action.setProperty(ALT_KEYS_PROPERTY, list(keys))
    if collapse_keys:
        action.setProperty(COLLAPSE_PROPERTY, True)
    parent.addAction(action)
    for key, slot in bindings:
        shortcut = QShortcut(QKeySequence(key), parent)
        shortcut.activated.connect(slot)
        shortcut.activatedAmbiguously.connect(
            lambda k=key: _on_shortcut_ambiguous(k)
        )
    return action


def collect_live_shortcuts(root: QWidget) -> list[tuple[str, str, str]]:
    """Return all live key sequence bindings across root shortcuts and actions.

    Returns a list of tuples: (normalized_key_string, context_description, owner_description).
    """
    native = QKeySequence.SequenceFormat.NativeText
    results: list[tuple[str, str, str]] = []

    # 1. QShortcut instances attached to root or its descendants
    for shortcut in root.findChildren(QShortcut):
        if not shortcut.isEnabled():
            continue
        key_str = shortcut.key().toString(native)
        if not key_str:
            continue
        parent = shortcut.parent()
        parent_name = (
            parent.objectName() or parent.__class__.__name__
            if parent is not None
            else "unknown"
        )
        context = str(shortcut.context())
        results.append((key_str, context, f"QShortcut({parent_name})"))

    # 2. QAction instances attached to root or its descendants with active shortcuts
    for action in root.findChildren(QAction):
        if action.shortcut().isEmpty():
            continue
        # Documentation rows must not bind shortcuts; if they have receivers or triggers,
        # count them as live actions
        has_receiver = action.receivers(SIGNAL("triggered(bool)")) > 0
        if not has_receiver and action.property(SECTION_PROPERTY):
            # Pure untriggered documentation action
            continue
        key_str = action.shortcut().toString(native)
        if not key_str:
            continue
        owner = action.text().replace("&", "") or str(action.property(LABEL_PROPERTY)) or "QAction"
        context = str(action.shortcutContext())
        results.append((key_str, context, f"QAction({owner})"))

    return results
