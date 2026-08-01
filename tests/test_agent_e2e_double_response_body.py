"""PYPOST-889: Agent e2e lock — response body appears exactly once after Send.

Drives the PYPOST-887 reported case (PUT + malformed nested JSON-like body)
through the agent UI path with a deterministic HTTP stub. Asserts the response
panel shows the stub body token exactly once (not duplicated by a late chunk
flush after ``display_response``).

Default HEAD (discard present) is green. FR5 red proof (PYPOST-892):
``test_agent_e2e_double_body_red_path_without_discard`` monkeypatches
``_discard_chunk_buffer`` to a no-op and asserts ``count >= 2``.
"""

from __future__ import annotations

import pytest
from PySide6.QtTest import QTest

from pypost.agent import AgentAppSession, find_widget
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
from tests.helpers.agent_e2e_send_settle import wait_response_after_send

pytestmark = [
    pytest.mark.timeout(60),
    pytest.mark.agent_e2e,
]

# Past presenter chunk flush (33 ms) so late append would be visible if present.
_CHUNK_FLUSH_SETTLE_MS = 100
_STATUS_LABEL = f"Status: {LOCK_DOUBLE_BODY_STATUS}"


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
        wait_response_after_send(
            session,
            status_label=_STATUS_LABEL,
            body_text=LOCK_DOUBLE_BODY,
            step="wait_response_after_send",
            message_prefix="double-body lock Send settle failed",
        )
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


def test_agent_e2e_double_body_red_path_without_discard(
    agent_e2e_session: AgentAppSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PYPOST-892 FR5: no-op discard → body token appears at least twice."""
    from pypost.ui.presenters.tabs_presenter_worker import (
        TabsPresenterWorkerHandlers,
    )

    monkeypatch.setattr(
        TabsPresenterWorkerHandlers,
        "_discard_chunk_buffer",
        lambda self, tab: None,
    )

    session = agent_e2e_session
    assert session.window.is_ui_ready is True
    session.ui_fill(URL_INPUT, LOCK_DOUBLE_BODY_URL)
    session.ui_select(METHOD_COMBO, LOCK_DOUBLE_BODY_METHOD)
    session.ui_fill(REQUEST_BODY_EDIT, LOCK_DOUBLE_BODY_REQUEST)

    stub = canned_send_with_one_chunk(CANNED_DOUBLE_BODY_LOCK_OK)
    with stub_agent_e2e_http(stub, name="double_body_lock_ok"):
        session.ui_click(SEND_BUTTON)
        wait_response_after_send(
            session,
            status_label=_STATUS_LABEL,
            body_text=LOCK_DOUBLE_BODY,
            step="wait_response_after_send",
            message_prefix="double-body red-path Send settle failed",
        )
        QTest.qWait(_CHUNK_FLUSH_SETTLE_MS)
        snap = session.ui_snapshot()

    joined = joined_panel_values(snap)
    count = joined.count(LOCK_DOUBLE_BODY)
    assert count >= 2, (
        f"FR5 red proof expected count>=2 without discard "
        f"(got count={count}); excerpt={response_panel_excerpt(snap)!r}"
    )
