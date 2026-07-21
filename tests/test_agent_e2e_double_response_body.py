"""PYPOST-889: Agent e2e lock — response body appears exactly once after Send.

Drives the PYPOST-887 reported case (PUT + malformed nested JSON-like body)
through the agent UI path with a deterministic HTTP stub. Asserts the response
panel shows the stub body token exactly once (not duplicated by a late chunk
flush after ``display_response``).

Default HEAD (discard present) is green. FR5 red proof: temporarily no-op
``_discard_chunk_buffer`` in ``_on_request_finished`` while keeping the
streaming stub that arms the flush timer.
"""

from __future__ import annotations

from typing import Any

import pytest
from PySide6.QtTest import QTest

from pypost.agent import AgentAppSession, UiWaitTimeoutError, find_widget
from pypost.fixtures.agent_e2e_http import (
    CANNED_DOUBLE_BODY_LOCK_OK,
    LOCK_DOUBLE_BODY,
    LOCK_DOUBLE_BODY_METHOD,
    LOCK_DOUBLE_BODY_REQUEST,
    LOCK_DOUBLE_BODY_STATUS,
    LOCK_DOUBLE_BODY_URL,
    canned_send_with_one_chunk,
    stub_agent_e2e_http,
)
from pypost.ui.widget_ids import (
    METHOD_COMBO,
    REQUEST_BODY_EDIT,
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

# Past presenter chunk flush (33 ms) so late append would be visible if present.
_CHUNK_FLUSH_SETTLE_MS = 100
_SEND_SETTLE_TIMEOUT_S = 15.0

_STATUS_LABEL = f"Status: {LOCK_DOUBLE_BODY_STATUS}"


def _response_ready(snap: dict[str, Any]) -> bool:
    joined = joined_panel_values(snap)
    return _STATUS_LABEL in joined and LOCK_DOUBLE_BODY in joined


def test_agent_e2e_response_body_appears_exactly_once(
    agent_e2e_session: AgentAppSession,
) -> None:
    """PUT + reported body shape → stubbed Send → body token count == 1."""
    session = agent_e2e_session
    assert session.window.is_ui_ready is True
    find_widget(session.window, URL_INPUT)
    find_widget(session.window, METHOD_COMBO)
    find_widget(session.window, SEND_BUTTON)
    find_widget(session.window, REQUEST_BODY_EDIT)

    session.ui_fill(URL_INPUT, LOCK_DOUBLE_BODY_URL)
    session.ui_select(METHOD_COMBO, LOCK_DOUBLE_BODY_METHOD)
    # PUT auto-switches to Body tab so the editor is visible for ui_fill.
    session.ui_fill(REQUEST_BODY_EDIT, LOCK_DOUBLE_BODY_REQUEST)

    stub = canned_send_with_one_chunk(CANNED_DOUBLE_BODY_LOCK_OK)
    with stub_agent_e2e_http(stub, name="double_body_lock_ok"):
        session.ui_click(SEND_BUTTON)
        try:
            session.wait_for_snapshot(
                _response_ready,
                timeout=_SEND_SETTLE_TIMEOUT_S,
            )
        except UiWaitTimeoutError as exc:
            last = session.ui_snapshot()
            excerpt = response_panel_excerpt(last)
            raise UiWaitTimeoutError(
                f"double-body lock Send settle failed: {exc}; "
                f"response_excerpt={excerpt!r}",
                timeout_s=exc.timeout_s,
                condition=exc.condition,
                diagnostics={
                    **exc.diagnostics,
                    "step": "wait_response_after_send",
                    "response_excerpt": excerpt,
                },
            ) from exc
        # Allow a pending chunk flush to fire if discard were missing (FR5).
        QTest.qWait(_CHUNK_FLUSH_SETTLE_MS)
        snap = session.ui_snapshot()

    panel = subtree_by_name(snap, RESPONSE_PANEL)
    excerpt = response_panel_excerpt(snap)
    assert panel is not None, (
        f"RESPONSE_PANEL missing after Send; excerpt={excerpt!r}"
    )
    joined = joined_panel_values(snap)
    count = joined.count(LOCK_DOUBLE_BODY)
    assert count == 1, (
        f"expected response body {LOCK_DOUBLE_BODY!r} exactly once "
        f"(got count={count}; double-body regression if count>=2); "
        f"excerpt={excerpt!r}"
    )
