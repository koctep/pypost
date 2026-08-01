"""PYPOST-958: GUI same-URL GET+POST under compound-key Mapping stub."""

from __future__ import annotations

import json
from typing import Any

import pytest

from pypost.agent import AgentAppSession, find_widget
from pypost.fixtures.agent_e2e_http import (
    CANNED_SEED_GET_OK,
    SEED_GET_OK_BODY,
    SEED_GET_RESOLVED_URL,
    SEED_POST_OK_BODY,
    make_canned_http_result,
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
from tests.helpers.agent_e2e_send_settle import wait_response_after_snapshot

pytestmark = [
    pytest.mark.timeout(60),
    pytest.mark.agent_e2e,
]

_COMPOUND_SETTLE_PREFIX = "mapping compound-key Send settle failed"
_STATUS_LABEL = "Status: 200"
_GET_BODY_IN_SNAPSHOT = json.dumps(
    json.loads(SEED_GET_OK_BODY), ensure_ascii=False
)
_POST_BODY_IN_SNAPSHOT = json.dumps(
    json.loads(SEED_POST_OK_BODY), ensure_ascii=False
)
_SHARED_URL = SEED_GET_RESOLVED_URL
_CANNED_SHARED_POST_OK = make_canned_http_result(
    url=_SHARED_URL,
    body=SEED_POST_OK_BODY,
    resolved_body=SEED_POST_BODY,
)


def _get_response_ready(snap: dict[str, Any]) -> bool:
    joined = joined_panel_values(snap)
    return _STATUS_LABEL in joined and _GET_BODY_IN_SNAPSHOT in joined


def _post_response_ready(snap: dict[str, Any]) -> bool:
    joined = joined_panel_values(snap)
    return _STATUS_LABEL in joined and _POST_BODY_IN_SNAPSHOT in joined


def test_mapping_compound_keys_same_url_get_post_panel_outcomes(
    agent_e2e_session: AgentAppSession,
    agent_e2e_http_stub: Any,
) -> None:
    """FR1–FR4: GET+POST to one URL under compound-key map assert panel."""
    session = agent_e2e_session
    assert session.window.is_ui_ready is True
    find_widget(session.window, URL_INPUT)
    find_widget(session.window, METHOD_COMBO)
    find_widget(session.window, SEND_BUTTON)
    find_widget(session.window, REQUEST_BODY_EDIT)

    responses = {
        f"GET {_SHARED_URL}": CANNED_SEED_GET_OK,
        f"POST {_SHARED_URL}": _CANNED_SHARED_POST_OK,
    }

    with agent_e2e_http_stub(responses):
        session.ui_fill(URL_INPUT, _SHARED_URL)
        session.ui_select(METHOD_COMBO, "GET")
        session.ui_click(SEND_BUTTON)
        get_snap = wait_response_after_snapshot(
            session,
            _get_response_ready,
            step="wait_response_after_mapping_compound_get_send",
            message_prefix=_COMPOUND_SETTLE_PREFIX,
        )

        session.ui_fill(URL_INPUT, _SHARED_URL)
        session.ui_select(METHOD_COMBO, "POST")
        session.ui_fill(REQUEST_BODY_EDIT, SEED_POST_BODY)
        session.ui_click(SEND_BUTTON)
        post_snap = wait_response_after_snapshot(
            session,
            _post_response_ready,
            step="wait_response_after_mapping_compound_post_send",
            message_prefix=_COMPOUND_SETTLE_PREFIX,
        )

    assert subtree_by_name(get_snap, RESPONSE_PANEL) is not None
    get_joined = joined_panel_values(get_snap)
    assert _STATUS_LABEL in get_joined
    assert _GET_BODY_IN_SNAPSHOT in get_joined

    assert subtree_by_name(post_snap, RESPONSE_PANEL) is not None
    post_joined = joined_panel_values(post_snap)
    assert _STATUS_LABEL in post_joined
    assert _POST_BODY_IN_SNAPSHOT in post_joined
    assert stub_agent_e2e_http is agent_e2e_http_stub
