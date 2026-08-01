"""PYPOST-859 / PYPOST-904: Env-pack Send uses shared HTTP stub + seed URL."""

from __future__ import annotations

import json
import logging
from typing import Any

import pytest

from pypost.agent import AgentAppSession, find_widget
from pypost.fixtures.agent_e2e_http import (
    CANNED_SEED_GET_OK,
    SEED_GET_OK_BODY,
    SEED_GET_RESOLVED_URL,
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
    subtree_by_name,
)
from tests.helpers.agent_e2e_send_settle import (
    json_response_body_display,
    wait_response_after_send,
)

pytestmark = [
    pytest.mark.timeout(60),
    pytest.mark.agent_e2e,
]

_HTTP_LOGGER = "pypost.fixtures.agent_e2e_http"
_STUB_INSTALLED_SEED_GET = "agent_e2e_http_stub_installed name=seed_get_ok"

_STATUS_LABEL = "Status: 200"
_BODY_DISPLAY = json_response_body_display(SEED_GET_OK_BODY)
# Snapshot join still carries compact JSON from sanitize; post-settle only.
_BODY_IN_SNAPSHOT = json.dumps(json.loads(SEED_GET_OK_BODY), ensure_ascii=False)


def test_seeded_env_send_uses_shared_http_stub(
    seeded_agent_e2e_session: AgentAppSession,
    agent_e2e_http_stub: Any,
) -> None:
    """FR4: seeded session + shared HTTP layer for seed GET Send."""
    session = seeded_agent_e2e_session
    assert session.window.is_ui_ready is True
    find_widget(session.window, URL_INPUT)
    find_widget(session.window, METHOD_COMBO)
    find_widget(session.window, SEND_BUTTON)

    session.ui_fill(URL_INPUT, SEED_GET_RESOLVED_URL)
    session.ui_select(METHOD_COMBO, "GET")

    # Prefer fixture entry; equivalent to stub_agent_e2e_http(...).
    with agent_e2e_http_stub(CANNED_SEED_GET_OK):
        session.ui_click(SEND_BUTTON)
        wait_response_after_send(
            session,
            status_label=_STATUS_LABEL,
            body_text=_BODY_DISPLAY,
            step="wait_response_after_seed_send",
            message_prefix="env seed Send settle failed",
        )
        snap = session.ui_snapshot()

    panel = subtree_by_name(snap, RESPONSE_PANEL)
    assert panel is not None
    joined = joined_panel_values(snap)
    assert _STATUS_LABEL in joined
    assert _BODY_IN_SNAPSHOT in joined
    # Catalog entry still importable for authors extending scenarios.
    assert stub_agent_e2e_http is agent_e2e_http_stub


def test_seeded_env_send_logs_http_stub_installed(
    seeded_agent_e2e_session: AgentAppSession,
    agent_e2e_http_stub: Any,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """PYPOST-904: GUI Send path emits agent_e2e_http_stub_installed under caplog."""
    session = seeded_agent_e2e_session
    assert session.window.is_ui_ready is True

    session.ui_fill(URL_INPUT, SEED_GET_RESOLVED_URL)
    session.ui_select(METHOD_COMBO, "GET")

    with caplog.at_level(logging.INFO, logger=_HTTP_LOGGER):
        with agent_e2e_http_stub(CANNED_SEED_GET_OK):
            session.ui_click(SEND_BUTTON)
            wait_response_after_send(
                session,
                status_label=_STATUS_LABEL,
                body_text=_BODY_DISPLAY,
                step="wait_response_after_seed_send_caplog_smoke",
                message_prefix="env seed Send caplog smoke settle failed",
            )

    assert _STUB_INSTALLED_SEED_GET in caplog.text
