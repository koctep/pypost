"""PYPOST-901: GUI multi-URL Send using one Mapping stub."""

from __future__ import annotations

import json
import logging
from typing import Any

import pytest

from pypost.agent import AgentAppSession, UiWaitTimeoutError, find_widget
from pypost.fixtures.agent_e2e_http import (
    CANNED_SEED_GET_OK,
    CANNED_SEED_POST_OK,
    SEED_GET_OK_BODY,
    SEED_GET_RESOLVED_URL,
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
from tests.helpers.agent_e2e_send_settle import wait_response_after_snapshot
from tests.helpers.agent_e2e_timeouts import FORCED_SETTLE_TIMEOUT_S

pytestmark = [
    pytest.mark.timeout(60),
    pytest.mark.agent_e2e,
]

_MAPPING_SETTLE_PREFIX = "mapping multi-URL Send settle failed"
_HTTP_LOGGER = "pypost.fixtures.agent_e2e_http"
_STUB_INSTALLED_URL_ROUTER = "agent_e2e_http_stub_installed name=url_router"

_STATUS_LABEL = "Status: 200"
_GET_BODY_IN_SNAPSHOT = json.dumps(
    json.loads(SEED_GET_OK_BODY), ensure_ascii=False
)
_POST_BODY_IN_SNAPSHOT = json.dumps(
    json.loads(SEED_POST_OK_BODY), ensure_ascii=False
)


def _get_response_ready(snap: dict[str, Any]) -> bool:
    joined = joined_panel_values(snap)
    return _STATUS_LABEL in joined and _GET_BODY_IN_SNAPSHOT in joined


def _post_response_ready(snap: dict[str, Any]) -> bool:
    joined = joined_panel_values(snap)
    return _STATUS_LABEL in joined and _POST_BODY_IN_SNAPSHOT in joined


def test_mapping_stub_two_distinct_urls_panel_outcomes(
    agent_e2e_session: AgentAppSession,
    agent_e2e_http_stub: Any,
) -> None:
    """FR1–FR4: two Sends under one Mapping stub assert panel outcomes."""
    session = agent_e2e_session
    assert session.window.is_ui_ready is True
    find_widget(session.window, URL_INPUT)
    find_widget(session.window, METHOD_COMBO)
    find_widget(session.window, SEND_BUTTON)
    find_widget(session.window, REQUEST_BODY_EDIT)

    responses = {
        SEED_GET_RESOLVED_URL: CANNED_SEED_GET_OK,
        SEED_POST_RESOLVED_URL: CANNED_SEED_POST_OK,
    }

    with agent_e2e_http_stub(responses):
        session.ui_fill(URL_INPUT, SEED_GET_RESOLVED_URL)
        session.ui_select(METHOD_COMBO, "GET")
        session.ui_click(SEND_BUTTON)
        get_snap = wait_response_after_snapshot(
            session,
            _get_response_ready,
            step="wait_response_after_mapping_get_send",
            message_prefix=_MAPPING_SETTLE_PREFIX,
        )

        session.ui_fill(URL_INPUT, SEED_POST_RESOLVED_URL)
        session.ui_select(METHOD_COMBO, "POST")
        session.ui_fill(REQUEST_BODY_EDIT, SEED_POST_BODY)
        session.ui_click(SEND_BUTTON)
        post_snap = wait_response_after_snapshot(
            session,
            _post_response_ready,
            step="wait_response_after_mapping_post_send",
            message_prefix=_MAPPING_SETTLE_PREFIX,
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


def test_mapping_send_logs_http_stub_installed_url_router(
    agent_e2e_session: AgentAppSession,
    agent_e2e_http_stub: Any,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """PYPOST-957: Mapping GUI Send path emits url_router install under caplog."""
    session = agent_e2e_session
    assert session.window.is_ui_ready is True
    find_widget(session.window, URL_INPUT)
    find_widget(session.window, METHOD_COMBO)
    find_widget(session.window, SEND_BUTTON)

    responses = {
        SEED_GET_RESOLVED_URL: CANNED_SEED_GET_OK,
    }

    with caplog.at_level(logging.INFO, logger=_HTTP_LOGGER):
        with agent_e2e_http_stub(responses):
            session.ui_fill(URL_INPUT, SEED_GET_RESOLVED_URL)
            session.ui_select(METHOD_COMBO, "GET")
            session.ui_click(SEND_BUTTON)
            wait_response_after_snapshot(
                session,
                _get_response_ready,
                step="wait_response_after_mapping_get_send_caplog_smoke",
                message_prefix=_MAPPING_SETTLE_PREFIX,
            )

    assert _STUB_INSTALLED_URL_ROUTER in caplog.text


def test_mapping_get_send_settle_timeout_includes_step_and_excerpt(
    agent_e2e_session: AgentAppSession,
    agent_e2e_http_stub: Any,
) -> None:
    """PYPOST-955: forced mapping GET Send settle timeout carries step + excerpt."""
    session = agent_e2e_session
    assert session.window.is_ui_ready is True
    find_widget(session.window, URL_INPUT)
    find_widget(session.window, METHOD_COMBO)
    find_widget(session.window, SEND_BUTTON)

    responses = {
        SEED_GET_RESOLVED_URL: CANNED_SEED_GET_OK,
    }

    with agent_e2e_http_stub(responses):
        session.ui_fill(URL_INPUT, SEED_GET_RESOLVED_URL)
        session.ui_select(METHOD_COMBO, "GET")
        session.ui_click(SEND_BUTTON)
        with pytest.raises(UiWaitTimeoutError) as exc_info:
            wait_response_after_snapshot(
                session,
                lambda _: False,
                step="wait_response_after_mapping_get_send",
                message_prefix=_MAPPING_SETTLE_PREFIX,
                timeout=FORCED_SETTLE_TIMEOUT_S,
            )

    diagnostics = exc_info.value.diagnostics
    assert diagnostics.get("step") == "wait_response_after_mapping_get_send"
    assert "response_excerpt" in diagnostics
    assert isinstance(diagnostics["response_excerpt"], str)


def test_mapping_post_send_settle_timeout_includes_step_and_excerpt(
    agent_e2e_session: AgentAppSession,
    agent_e2e_http_stub: Any,
) -> None:
    """PYPOST-982: forced mapping POST Send settle timeout carries step + excerpt."""
    session = agent_e2e_session
    assert session.window.is_ui_ready is True
    find_widget(session.window, URL_INPUT)
    find_widget(session.window, METHOD_COMBO)
    find_widget(session.window, SEND_BUTTON)
    find_widget(session.window, REQUEST_BODY_EDIT)

    responses = {
        SEED_POST_RESOLVED_URL: CANNED_SEED_POST_OK,
    }

    with agent_e2e_http_stub(responses):
        session.ui_fill(URL_INPUT, SEED_POST_RESOLVED_URL)
        session.ui_select(METHOD_COMBO, "POST")
        session.ui_fill(REQUEST_BODY_EDIT, SEED_POST_BODY)
        session.ui_click(SEND_BUTTON)
        with pytest.raises(UiWaitTimeoutError) as exc_info:
            wait_response_after_snapshot(
                session,
                lambda _: False,
                step="wait_response_after_mapping_post_send",
                message_prefix=_MAPPING_SETTLE_PREFIX,
                timeout=FORCED_SETTLE_TIMEOUT_S,
            )

    diagnostics = exc_info.value.diagnostics
    assert diagnostics.get("step") == "wait_response_after_mapping_post_send"
    assert isinstance(diagnostics.get("response_excerpt"), str)
    assert diagnostics["response_excerpt"]
