"""Shared product-dialog settle helpers for agent e2e (PYPOST-936)."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from pypost.agent import AgentAppSession, UiWaitTimeoutError

__all__ = [
    "modal_diag",
    "run_product_dialog_settle",
]


def modal_diag() -> dict[str, object]:
    """Scalar modal context for timeout diagnostics."""
    modal = QApplication.activeModalWidget()
    return {
        "dialog_title": modal.windowTitle() if modal is not None else None,
        "dialog_object_name": modal.objectName() if modal is not None else None,
        "active_modal_type": type(modal).__name__ if modal is not None else None,
    }


def _rewrap_dialog_settle_timeout(exc: UiWaitTimeoutError, *, step: str) -> UiWaitTimeoutError:
    return UiWaitTimeoutError(
        f"dialog settle failed: {exc}",
        timeout_s=exc.timeout_s,
        condition=exc.condition,
        diagnostics={
            **exc.diagnostics,
            "step": step,
            **modal_diag(),
        },
    )


def _dismiss_active_modal() -> None:
    modal = QApplication.activeModalWidget()
    if modal is not None:
        modal.reject()


def run_product_dialog_settle(
    session: AgentAppSession,
    *,
    click_widget_id: str,
    wait_condition: Callable[[], bool],
    timeout: float,
    message: str,
    condition_name: str,
    step: str,
) -> tuple[bool, list[BaseException]]:
    """Timer-before-click modal settle; returns ``(settled_ok, callback_errors)``."""
    settle_ok = False
    settle_error: list[BaseException] = []

    def _on_settle() -> None:
        nonlocal settle_ok
        try:
            try:
                session.wait_until(
                    wait_condition,
                    timeout=timeout,
                    message=message,
                    condition_name=condition_name,
                )
            except UiWaitTimeoutError as exc:
                raise _rewrap_dialog_settle_timeout(exc, step=step) from exc
            settle_ok = True
        except BaseException as exc:
            settle_error.append(exc)
        finally:
            _dismiss_active_modal()

    QTimer.singleShot(0, _on_settle)
    session.ui_click(click_widget_id)
    return settle_ok, settle_error
