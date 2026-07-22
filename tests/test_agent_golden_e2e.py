"""PYPOST-838/859: Golden e2e — agent completes one request/response flow."""

from __future__ import annotations

import json
from typing import Any

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
    RESPONSE_PANEL,
    SEND_BUTTON,
    URL_INPUT,
)
from tests.helpers.agent_e2e_response_panel import (
    joined_panel_values,
    response_panel_excerpt,
    subtree_by_name,
)

pytestmark = [
    pytest.mark.timeout(60),
    pytest.mark.agent_e2e,
]

FIXTURE_URL = GOLDEN_URL
FIXTURE_METHOD = GOLDEN_METHOD
FIXTURE_STATUS = GOLDEN_STATUS
FIXTURE_BODY = GOLDEN_BODY
# Snapshot sanitize_text re-dumps JSON without indent; assert that form.
FIXTURE_BODY_IN_SNAPSHOT = json.dumps(
    json.loads(FIXTURE_BODY), ensure_ascii=False
)
FIXTURE_STATUS_LABEL = f"Status: {FIXTURE_STATUS}"

_SEND_SETTLE_TIMEOUT_S = 15.0


def _response_ready(snap: dict[str, Any]) -> bool:
    joined = joined_panel_values(snap)
    return (
        FIXTURE_STATUS_LABEL in joined
        and FIXTURE_BODY_IN_SNAPSHOT in joined
    )


def _assert_response_ui(snap: dict[str, Any]) -> None:
    panel = subtree_by_name(snap, RESPONSE_PANEL)
    excerpt = response_panel_excerpt(snap)
    assert panel is not None, (
        f"RESPONSE_PANEL missing after Send; excerpt={excerpt!r}"
    )
    joined = joined_panel_values(snap)
    assert FIXTURE_STATUS_LABEL in joined, (
        f"expected {FIXTURE_STATUS_LABEL!r} in response UI; "
        f"excerpt={excerpt!r}"
    )
    assert FIXTURE_BODY_IN_SNAPSHOT in joined, (
        f"expected body {FIXTURE_BODY_IN_SNAPSHOT!r} in response UI; "
        f"excerpt={excerpt!r}"
    )


def test_agent_golden_request_response_flow(
    agent_e2e_session: AgentAppSession,
) -> None:
    """Compose lifecycle + identity + actions + wait + snapshot for Send → 200."""
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
            snap = session.wait_for_snapshot(
                _response_ready,
                timeout=_SEND_SETTLE_TIMEOUT_S,
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

    _assert_response_ui(snap)
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
