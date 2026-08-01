"""PYPOST-838/859: Golden e2e — agent completes one request/response flow."""

from __future__ import annotations

import json

import pytest

from pypost.agent import AgentAppSession, UiWaitTimeoutError, find_widget
from pypost.fixtures.agent_e2e_http import (
    CANNED_GOLDEN_OK,
    GOLDEN_BODY,
    GOLDEN_METHOD,
    GOLDEN_STATUS,
    GOLDEN_URL,
    stub_agent_e2e_http,
)
from pypost.ui.widget_ids import (
    METHOD_COMBO,
    RESPONSE_BODY,
    RESPONSE_STATUS,
    SEND_BUTTON,
    URL_INPUT,
)
from tests.helpers.agent_e2e_send import SEND_SETTLE_TIMEOUT_S
from tests.helpers.agent_e2e_response_panel import response_panel_excerpt

pytestmark = [
    pytest.mark.timeout(60),
    pytest.mark.agent_e2e,
]

FIXTURE_URL = GOLDEN_URL
FIXTURE_METHOD = GOLDEN_METHOD
FIXTURE_STATUS = GOLDEN_STATUS
FIXTURE_BODY = GOLDEN_BODY
# Display form matches ResponseView.display_response default indent_size=2.
FIXTURE_BODY_DISPLAY = json.dumps(json.loads(FIXTURE_BODY), indent=2)
FIXTURE_STATUS_LABEL = f"Status: {FIXTURE_STATUS}"


def test_agent_golden_request_response_flow(
    agent_e2e_session: AgentAppSession,
) -> None:
    """Compose lifecycle + identity + actions + text wait for Send → 200."""
    session = agent_e2e_session
    assert session.window.is_ui_ready is True
    find_widget(session.window, URL_INPUT)
    find_widget(session.window, METHOD_COMBO)
    find_widget(session.window, SEND_BUTTON)

    session.ui_fill(URL_INPUT, FIXTURE_URL)
    session.ui_select(METHOD_COMBO, FIXTURE_METHOD)

    with stub_agent_e2e_http(CANNED_GOLDEN_OK):
        session.ui_click(SEND_BUTTON)
        try:
            session.wait_for_text(
                RESPONSE_STATUS,
                FIXTURE_STATUS_LABEL,
                timeout=SEND_SETTLE_TIMEOUT_S,
            )
            session.wait_for_text(
                RESPONSE_BODY,
                FIXTURE_BODY_DISPLAY,
                timeout=SEND_SETTLE_TIMEOUT_S,
            )
        except UiWaitTimeoutError as exc:
            last = session.ui_snapshot()
            excerpt = response_panel_excerpt(last)
            raise UiWaitTimeoutError(
                f"golden Send settle failed: {exc}; "
                f"response_excerpt={excerpt!r}",
                timeout_s=exc.timeout_s,
                condition=exc.condition,
                diagnostics={
                    **exc.diagnostics,
                    "step": "wait_response_after_send",
                    "response_excerpt": excerpt,
                },
            ) from exc

    assert CANNED_GOLDEN_OK.response.status_code == FIXTURE_STATUS


def test_agent_golden_settle_timeout_includes_step_and_excerpt(
    agent_e2e_session: AgentAppSession,
) -> None:
    """PYPOST-853 TD-3: forced settle timeout carries step + response_excerpt."""
    session = agent_e2e_session
    assert session.window.is_ui_ready is True
    session.ui_fill(URL_INPUT, FIXTURE_URL)
    session.ui_select(METHOD_COMBO, FIXTURE_METHOD)

    with stub_agent_e2e_http(CANNED_GOLDEN_OK):
        session.ui_click(SEND_BUTTON)
        with pytest.raises(UiWaitTimeoutError) as exc_info:
            try:
                session.wait_for_snapshot(lambda _snap: False, timeout=0.05)
            except UiWaitTimeoutError as exc:
                last = session.ui_snapshot()
                excerpt = response_panel_excerpt(last)
                raise UiWaitTimeoutError(
                    f"golden Send settle failed: {exc}; "
                    f"response_excerpt={excerpt!r}",
                    timeout_s=exc.timeout_s,
                    condition=exc.condition,
                    diagnostics={
                        **exc.diagnostics,
                        "step": "wait_response_after_send",
                        "response_excerpt": excerpt,
                    },
                ) from exc

    diagnostics = exc_info.value.diagnostics
    assert diagnostics.get("step") == "wait_response_after_send"
    assert "response_excerpt" in diagnostics
    assert isinstance(diagnostics["response_excerpt"], str)
