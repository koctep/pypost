"""Settle/wait helpers for agent UI flows (PYPOST-837).

Bounded ``processEvents`` polling for common post-action conditions. Production
code must use this module — never ``tests.helpers``.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any, Final

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import (
    QComboBox,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QTextEdit,
    QWidget,
)

from pypost.agent.ui_actions import UiTargetNotFoundError, find_widget
from pypost.agent.ui_snapshot import capture_ui_snapshot, count_snapshot_nodes

logger = logging.getLogger(__name__)

DEFAULT_UI_WAIT_TIMEOUT_S: Final[float] = 10.0
DEFAULT_UI_WAIT_INTERVAL_S: Final[float] = 0.05

# Cap diagnostic text snippets so timeout messages stay actionable, not huge.
_DIAG_TEXT_MAX: Final[int] = 80


class UiWaitTimeoutError(TimeoutError):
    """Raised when a UI wait budget expires without the condition becoming true."""

    def __init__(
        self,
        message: str,
        *,
        timeout_s: float,
        condition: str,
        diagnostics: dict[str, object] | None = None,
    ) -> None:
        self.timeout_s = timeout_s
        self.condition = condition
        self.diagnostics = dict(diagnostics or {})
        super().__init__(message)


def wait_until(
    condition: Callable[[], bool],
    *,
    timeout: float = DEFAULT_UI_WAIT_TIMEOUT_S,
    interval: float = DEFAULT_UI_WAIT_INTERVAL_S,
    message: str = "condition not met within timeout",
    condition_name: str = "predicate",
    diagnostics_factory: Callable[[], dict[str, object]] | None = None,
) -> None:
    """Process Qt events until ``condition()`` is true or ``timeout`` elapses.

    Args:
        condition: Poll predicate; return True when settled.
        timeout: Wall-clock seconds before failure (default
            ``DEFAULT_UI_WAIT_TIMEOUT_S``).
        interval: Sleep between polls (default ``DEFAULT_UI_WAIT_INTERVAL_S``).
        message: Human-readable failure prefix.
        condition_name: Short label for logs and ``UiWaitTimeoutError.condition``.
        diagnostics_factory: Optional callable invoked once on timeout to build
            a scalar diagnostics dict (never large trees).

    Raises:
        UiWaitTimeoutError: Condition never became true within ``timeout``.
    """
    deadline = time.monotonic() + timeout
    started = time.monotonic()
    while time.monotonic() < deadline:
        QCoreApplication.processEvents()
        if condition():
            waited_ms = int((time.monotonic() - started) * 1000)
            logger.debug(
                "ui_wait_settled condition=%s waited_ms=%s timeout_s=%s",
                condition_name,
                waited_ms,
                timeout,
            )
            return
        time.sleep(interval)

    diagnostics: dict[str, object] = {"timeout_s": timeout, "condition": condition_name}
    if diagnostics_factory is not None:
        try:
            diagnostics.update(diagnostics_factory())
        except Exception as exc:  # noqa: BLE001 — diagnostics must not mask timeout
            diagnostics["diagnostics_error"] = type(exc).__name__

    waited_ms = int((time.monotonic() - started) * 1000)
    logger.debug(
        "ui_wait_timeout condition=%s waited_ms=%s timeout_s=%s",
        condition_name,
        waited_ms,
        timeout,
    )
    detail_parts = [f"{key}={value!r}" for key, value in diagnostics.items()]
    detail = " ".join(detail_parts)
    raise UiWaitTimeoutError(
        f"{message} ({detail})",
        timeout_s=timeout,
        condition=condition_name,
        diagnostics=diagnostics,
    )


def _widget_text(widget: QWidget) -> str | None:
    if isinstance(widget, QLineEdit):
        return widget.text()
    if isinstance(widget, QComboBox):
        return widget.currentText()
    if isinstance(widget, (QPlainTextEdit, QTextEdit)):
        return widget.toPlainText()
    if isinstance(widget, (QLabel, QPushButton)):
        return widget.text()
    return None


def _clip(text: str) -> str:
    if len(text) <= _DIAG_TEXT_MAX:
        return text
    return text[:_DIAG_TEXT_MAX] + "…"


def wait_for_widget(
    root: QWidget,
    widget_id: str,
    *,
    timeout: float = DEFAULT_UI_WAIT_TIMEOUT_S,
    interval: float = DEFAULT_UI_WAIT_INTERVAL_S,
) -> QWidget:
    """Wait until a widget with ``widget_id`` exists under ``root``.

    Returns:
        The resolved widget.

    Raises:
        UiWaitTimeoutError: Widget never appeared within ``timeout``.
    """
    found: list[QWidget] = []

    def _ready() -> bool:
        try:
            found.clear()
            found.append(find_widget(root, widget_id))
            return True
        except UiTargetNotFoundError:
            return False

    def _diag() -> dict[str, object]:
        return {"widget_id": widget_id, "found": False}

    wait_until(
        _ready,
        timeout=timeout,
        interval=interval,
        message=f"widget did not appear: widget_id={widget_id!r}",
        condition_name="widget_exists",
        diagnostics_factory=_diag,
    )
    return found[0]


def wait_for_enabled(
    root: QWidget,
    widget_id: str,
    *,
    timeout: float = DEFAULT_UI_WAIT_TIMEOUT_S,
    interval: float = DEFAULT_UI_WAIT_INTERVAL_S,
) -> QWidget:
    """Wait until the named widget exists, is visible, and is enabled.

    Returns:
        The resolved widget.

    Raises:
        UiWaitTimeoutError: Condition never met within ``timeout``.
    """
    found: list[QWidget] = []

    def _ready() -> bool:
        try:
            widget = find_widget(root, widget_id)
        except UiTargetNotFoundError:
            found.clear()
            return False
        found.clear()
        found.append(widget)
        return bool(widget.isVisible() and widget.isEnabled())

    def _diag() -> dict[str, object]:
        if not found:
            return {
                "widget_id": widget_id,
                "found": False,
                "visible": False,
                "enabled": False,
            }
        widget = found[0]
        return {
            "widget_id": widget_id,
            "found": True,
            "visible": widget.isVisible(),
            "enabled": widget.isEnabled(),
        }

    wait_until(
        _ready,
        timeout=timeout,
        interval=interval,
        message=(
            f"widget not enabled: widget_id={widget_id!r}"
        ),
        condition_name="widget_enabled",
        diagnostics_factory=_diag,
    )
    return found[0]


def wait_for_text(
    root: QWidget,
    widget_id: str,
    expected: str | Callable[[str], bool],
    *,
    timeout: float = DEFAULT_UI_WAIT_TIMEOUT_S,
    interval: float = DEFAULT_UI_WAIT_INTERVAL_S,
) -> QWidget:
    """Wait until the named widget's text matches ``expected``.

    ``expected`` may be an exact string or a predicate ``(text) -> bool``.

    Returns:
        The resolved widget.

    Raises:
        UiWaitTimeoutError: Text never matched within ``timeout``.
    """
    found: list[QWidget] = []
    last_text: list[str | None] = [None]

    def _matches(text: str) -> bool:
        if callable(expected):
            return bool(expected(text))
        return text == expected

    def _ready() -> bool:
        try:
            widget = find_widget(root, widget_id)
        except UiTargetNotFoundError:
            found.clear()
            last_text[0] = None
            return False
        found.clear()
        found.append(widget)
        text = _widget_text(widget)
        last_text[0] = text
        if text is None:
            # Fast-fail: widget exists but has no text API (PYPOST-852).
            raise UiWaitTimeoutError(
                f"widget has no text API: widget_id={widget_id!r} "
                f"type={type(widget).__name__}",
                timeout_s=0.0,
                condition="no_text_api",
                diagnostics={
                    "widget_id": widget_id,
                    "widget_type": type(widget).__name__,
                    "found": True,
                },
            )
        return _matches(text)

    def _diag() -> dict[str, object]:
        expected_repr: object
        if callable(expected):
            expected_repr = getattr(expected, "__name__", "predicate")
        else:
            expected_repr = _clip(expected)
        current = last_text[0]
        return {
            "widget_id": widget_id,
            "found": bool(found),
            "expected": expected_repr,
            "actual_text": None if current is None else _clip(current),
        }

    wait_until(
        _ready,
        timeout=timeout,
        interval=interval,
        message=f"text did not match: widget_id={widget_id!r}",
        condition_name="text_matches",
        diagnostics_factory=_diag,
    )
    return found[0]


def wait_for_snapshot(
    root: QWidget,
    predicate: Callable[[dict[str, Any]], bool],
    *,
    timeout: float = DEFAULT_UI_WAIT_TIMEOUT_S,
    interval: float = DEFAULT_UI_WAIT_INTERVAL_S,
) -> dict[str, Any]:
    """Wait until ``predicate(capture_ui_snapshot(root))`` is true.

    Returns:
        The snapshot dict that satisfied the predicate.

    Raises:
        UiWaitTimeoutError: Predicate never true within ``timeout``.
    """
    last: list[dict[str, Any] | None] = [None]

    def _ready() -> bool:
        snap = capture_ui_snapshot(root)
        last[0] = snap
        return bool(predicate(snap))

    def _diag() -> dict[str, object]:
        snap = last[0]
        if snap is None:
            return {"has_snapshot": False}
        node_count, named_count = count_snapshot_nodes(snap)
        return {
            "has_snapshot": True,
            "node_count": node_count,
            "named_count": named_count,
            "root_name": snap.get("name") or "",
            "root_role": snap.get("role") or "",
        }

    wait_until(
        _ready,
        timeout=timeout,
        interval=interval,
        message="snapshot predicate not satisfied within timeout",
        condition_name="snapshot_predicate",
        diagnostics_factory=_diag,
    )
    assert last[0] is not None
    return last[0]
