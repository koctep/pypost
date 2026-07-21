"""Shared response-panel snapshot helpers for agent Send e2e tests.

Walk / subtree / excerpt / join helpers used by golden, env Send,
double-body lock, and presentation-matrix scenarios (PYPOST-869).
"""

from __future__ import annotations

from typing import Any

from pypost.ui.widget_ids import RESPONSE_PANEL

__all__ = [
    "joined_panel_values",
    "response_panel_excerpt",
    "subtree_by_name",
    "walk_values",
]


def walk_values(node: dict[str, Any]) -> list[str]:
    """Collect non-empty string ``value`` fields depth-first."""
    values: list[str] = []
    raw = node.get("value")
    if isinstance(raw, str) and raw:
        values.append(raw)
    for child in node.get("children") or []:
        if isinstance(child, dict):
            values.extend(walk_values(child))
    return values


def subtree_by_name(node: dict[str, Any], name: str) -> dict[str, Any] | None:
    """Return the first subtree whose ``name`` matches, or None."""
    if node.get("name") == name:
        return node
    for child in node.get("children") or []:
        if isinstance(child, dict):
            found = subtree_by_name(child, name)
            if found is not None:
                return found
    return None


def response_panel_excerpt(
    snap: dict[str, Any],
    *,
    max_len: int = 400,
) -> str:
    """Short `` | ``-joined RESPONSE_PANEL values for assert / timeout messages."""
    panel = subtree_by_name(snap, RESPONSE_PANEL)
    if panel is None:
        return "<response panel not in snapshot>"
    joined = " | ".join(walk_values(panel))
    if len(joined) > max_len:
        return joined[:max_len] + "…"
    return joined or "<response panel has no values>"


def joined_panel_values(snap: dict[str, Any]) -> str:
    """Newline-joined RESPONSE_PANEL values, or empty string if panel missing."""
    panel = subtree_by_name(snap, RESPONSE_PANEL)
    if panel is None:
        return ""
    return "\n".join(walk_values(panel))
