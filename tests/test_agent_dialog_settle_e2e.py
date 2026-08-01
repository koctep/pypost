"""PYPOST-919: product dialog settle after Settings open (agent_e2e).

Opens Settings via ``SETTINGS_BUTTON``, settles with shared modal-settle helper
(``run_product_dialog_settle`` — timer-before-click because modal ``exec()``
blocks ``ui_click``), then dismisses so the nested loop returns. Composition
proof only — not Settings functional coverage.
"""

from __future__ import annotations

import pytest

from pypost.agent import AgentAppSession, UiWaitTimeoutError, find_widget
from pypost.ui.widget_ids import SETTINGS_BUTTON, SETTINGS_DIALOG
from tests.helpers.agent_e2e_dialog_settle import run_product_dialog_settle

pytestmark = [
    pytest.mark.timeout(60),
    pytest.mark.agent_e2e,
]

DIALOG_SETTLE_TIMEOUT_S = 10.0
FORCED_SETTLE_TIMEOUT_S = 0.05
SETTLE_STEP = "wait_dialog_after_settings_open"


def _settings_dialog_present() -> bool:
    from PySide6.QtWidgets import QApplication

    modal = QApplication.activeModalWidget()
    if modal is None:
        return False
    return modal.objectName() == SETTINGS_DIALOG


def test_agent_dialog_settle_after_settings_open(
    agent_e2e_session: AgentAppSession,
) -> None:
    """Settle Settings dialog after open; dismiss before ``ui_click`` returns."""
    session = agent_e2e_session
    assert session.window.is_ui_ready is True
    find_widget(session.window, SETTINGS_BUTTON)

    settle_ok, settle_error = run_product_dialog_settle(
        session,
        click_widget_id=SETTINGS_BUTTON,
        wait_condition=_settings_dialog_present,
        timeout=DIALOG_SETTLE_TIMEOUT_S,
        message="settings dialog did not appear after SETTINGS_BUTTON click",
        condition_name="settings_dialog_present",
        step=SETTLE_STEP,
    )

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

    _settle_ok, settle_error = run_product_dialog_settle(
        session,
        click_widget_id=SETTINGS_BUTTON,
        wait_condition=lambda: False,
        timeout=FORCED_SETTLE_TIMEOUT_S,
        message="forced dialog settle timeout",
        condition_name="forced_dialog_settle_timeout",
        step=SETTLE_STEP,
    )

    assert len(settle_error) == 1
    assert isinstance(settle_error[0], UiWaitTimeoutError)
    diagnostics = settle_error[0].diagnostics
    assert diagnostics.get("step") == SETTLE_STEP
    assert "dialog_title" in diagnostics
    assert "dialog_object_name" in diagnostics
    assert "active_modal_type" in diagnostics
