"""PYPOST-871: Seed POST GUI Send uses shared HTTP stub + body fill."""

from __future__ import annotations

import json
from typing import Any

import pytest

from pypost.agent import AgentAppSession, UiWaitTimeoutError, find_widget
from pypost.fixtures.agent_e2e_http import (
    CANNED_SEED_POST_OK,
    SEED_POST_OK_BODY,
    SEED_POST_RESOLVED_URL,
    stub_agent_e2e_http,
)
from pypost.fixtures.agent_e2e_seed import SEED_POST_BODY
from pypost.ui.widget_ids import (
    METHOD_COMBO,
    REQUEST_BODY_EDIT,
    RESPONSE_PANEL,
    SEND_BUTTON,
    URL_INPUT,
)
from tests.helpers.agent_e2e_response_panel import (
    joined_panel_values,
    subtree_by_name,
)

pytestmark = [
    pytest.mark.timeout(60),
    pytest.mark.agent_e2e,
]

_STATUS_LABEL = "Status: 200"
_BODY_IN_SNAPSHOT = json.dumps(
    json.loads(SEED_POST_OK_BODY), ensure_ascii=False
)
_SEND_SETTLE_TIMEOUT_S = 15.0


def _response_ready(snap: dict[str, Any]) -> bool:
    joined = joined_panel_values(snap)
    return _STATUS_LABEL in joined and _BODY_IN_SNAPSHOT in joined


def test_seed_post_send_uses_shared_http_stub(
    agent_e2e_session: AgentAppSession,
    agent_e2e_http_stub: Any,
) -> None:
    """FR1–FR5: POST + body fill + shared HTTP stub for seed POST Send."""
    session = agent_e2e_session
    assert session.window.is_ui_ready is True
    find_widget(session.window, URL_INPUT)
    find_widget(session.window, METHOD_COMBO)
    find_widget(session.window, SEND_BUTTON)
    find_widget(session.window, REQUEST_BODY_EDIT)

    session.ui_fill(URL_INPUT, SEED_POST_RESOLVED_URL)
    session.ui_select(METHOD_COMBO, "POST")
    session.ui_fill(REQUEST_BODY_EDIT, SEED_POST_BODY)

    with agent_e2e_http_stub(CANNED_SEED_POST_OK):
        session.ui_click(SEND_BUTTON)
        try:
            snap = session.wait_for_snapshot(
                _response_ready,
                timeout=_SEND_SETTLE_TIMEOUT_S,
            )
        except UiWaitTimeoutError as exc:
            raise UiWaitTimeoutError(
                f"seed POST Send settle failed: {exc}",
                timeout_s=exc.timeout_s,
                condition=exc.condition,
                diagnostics={
                    **exc.diagnostics,
                    "step": "wait_response_after_seed_post_send",
                },
            ) from exc

    panel = subtree_by_name(snap, RESPONSE_PANEL)
    assert panel is not None
    joined = joined_panel_values(snap)
    assert _STATUS_LABEL in joined
    assert _BODY_IN_SNAPSHOT in joined
    assert stub_agent_e2e_http is agent_e2e_http_stub
