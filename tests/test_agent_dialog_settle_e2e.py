"""PYPOST-919: product dialog settle after Settings open (agent_e2e).

Opens Settings via ``SETTINGS_BUTTON``, settles with shared ``wait_until`` on
``QApplication.activeModalWidget()`` inside a ``QTimer.singleShot`` callback
(modal ``exec()`` blocks ``ui_click``), then dismisses so the nested loop
returns. Composition proof only — not Settings functional coverage.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from pypost.agent import AgentAppSession, UiWaitTimeoutError, find_widget
from pypost.ui.widget_ids import SETTINGS_BUTTON, SETTINGS_DIALOG

pytestmark = [
    pytest.mark.timeout(60),
    pytest.mark.agent_e2e,
]

DIALOG_SETTLE_TIMEOUT_S = 10.0
FORCED_SETTLE_TIMEOUT_S = 0.05
SETTLE_STEP = "wait_dialog_after_settings_open"


def _settings_dialog_present() -> bool:
    modal = QApplication.activeModalWidget()
    if modal is None:
        return False
    return modal.objectName() == SETTINGS_DIALOG


def _modal_diag() -> dict[str, object]:
    modal = QApplication.activeModalWidget()
    return {
        "dialog_title": modal.windowTitle() if modal is not None else None,
        "dialog_object_name": modal.objectName() if modal is not None else None,
        "active_modal_type": type(modal).__name__ if modal is not None else None,
    }


def test_agent_dialog_settle_after_settings_open(
    agent_e2e_session: AgentAppSession,
) -> None:
    """Settle Settings dialog after open; dismiss before ``ui_click`` returns."""
    session = agent_e2e_session
    assert session.window.is_ui_ready is True
    find_widget(session.window, SETTINGS_BUTTON)

    settle_ok = False
    settle_error: list[BaseException] = []

    def _on_dialog() -> None:
        nonlocal settle_ok
        try:
            try:
                session.wait_until(
                    _settings_dialog_present,
                    timeout=DIALOG_SETTLE_TIMEOUT_S,
                    message=(
                        "settings dialog did not appear after "
                        "SETTINGS_BUTTON click"
                    ),
                    condition_name="settings_dialog_present",
                )
            except UiWaitTimeoutError as exc:
                raise UiWaitTimeoutError(
                    f"dialog settle failed: {exc}",
                    timeout_s=exc.timeout_s,
                    condition=exc.condition,
                    diagnostics={
                        **exc.diagnostics,
                        "step": SETTLE_STEP,
                        **_modal_diag(),
                    },
                ) from exc
            settle_ok = True
        except BaseException as exc:
            settle_error.append(exc)
        finally:
            modal = QApplication.activeModalWidget()
            if modal is not None:
                modal.reject()

    QTimer.singleShot(0, _on_dialog)
    session.ui_click(SETTINGS_BUTTON)

    if settle_error:
        raise settle_error[0]
    assert settle_ok, "expected Settings dialog settle before dismiss"


def test_agent_dialog_settle_timeout_includes_step_and_modal_diag(
    agent_e2e_session: AgentAppSession,
) -> None:
    """PYPOST-934: forced dialog-settle timeout carries step + modal scalars."""
    session = agent_e2e_session
    assert session.window.is_ui_ready is True
    find_widget(session.window, SETTINGS_BUTTON)

    settle_error: list[BaseException] = []

    def _on_forced_timeout() -> None:
        try:
            try:
                session.wait_until(
                    lambda: False,
                    timeout=FORCED_SETTLE_TIMEOUT_S,
                    message="forced dialog settle timeout",
                    condition_name="forced_dialog_settle_timeout",
                )
            except UiWaitTimeoutError as exc:
                raise UiWaitTimeoutError(
                    f"dialog settle failed: {exc}",
                    timeout_s=exc.timeout_s,
                    condition=exc.condition,
                    diagnostics={
                        **exc.diagnostics,
                        "step": SETTLE_STEP,
                        **_modal_diag(),
                    },
                ) from exc
        except BaseException as exc:
            settle_error.append(exc)
        finally:
            modal = QApplication.activeModalWidget()
            if modal is not None:
                modal.reject()

    QTimer.singleShot(0, _on_forced_timeout)
    session.ui_click(SETTINGS_BUTTON)

    assert len(settle_error) == 1
    assert isinstance(settle_error[0], UiWaitTimeoutError)
    diagnostics = settle_error[0].diagnostics
    assert diagnostics.get("step") == SETTLE_STEP
    assert "dialog_title" in diagnostics
    assert "dialog_object_name" in diagnostics
    assert "active_modal_type" in diagnostics
