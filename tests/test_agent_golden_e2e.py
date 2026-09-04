"""PYPOST-838/859: Golden e2e — agent completes one request/response flow."""

from __future__ import annotations

import json

import pytest
from PySide6.QtWidgets import QApplication, QTabWidget

from pypost.agent import (
    AgentAppSession,
    UiWaitTimeoutError,
    find_widget,
)
from pypost.fixtures.agent_e2e_http import (
    CANNED_GOLDEN_OK,
    GOLDEN_BODY,
    GOLDEN_METHOD,
    GOLDEN_STATUS,
    GOLDEN_URL,
    stub_agent_e2e_http,
)
from pypost.ui.presenters.tabs_presenter import RequestTab
from pypost.ui.widget_ids import (
    METHOD_COMBO,
    PLUS_TAB_BUTTON,
    REQUEST_TABS,
    RESPONSE_STATUS,
    SEND_BUTTON,
    URL_INPUT,
)
from pypost.ui.widgets.new_tab_protocol_picker import TabProtocol
from tests.helpers.agent_e2e_response_panel import response_panel_excerpt
from tests.helpers.agent_e2e_send_settle import wait_response_after_send
from tests.helpers.agent_e2e_timeouts import FORCED_SETTLE_TIMEOUT_S

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


def _strip_request_tabs(session: AgentAppSession, qapp: QApplication) -> None:
    """Remove request tabs without presenter close (no auto blank replacement).

    Simulates restore that did not open a blank request tab: only the plus
    placeholder remains. ``removeTab`` does not destroy the page — destroy
    stripped tabs so window-scoped finds do not hit orphan role ids.
    """
    tabs = find_widget(session.window, REQUEST_TABS)
    assert isinstance(tabs, QTabWidget)
    orphans: list[RequestTab] = []
    for index in range(tabs.count() - 1, -1, -1):
        page = tabs.widget(index)
        if isinstance(page, RequestTab):
            tabs.removeTab(index)
            orphans.append(page)
    for page in orphans:
        page.setParent(None)
        page.deleteLater()
    orphans.clear()
    qapp.processEvents()
    assert not any(
        isinstance(tabs.widget(i), RequestTab) for i in range(tabs.count())
    )


def _inject_http_protocol_picker(session: AgentAppSession) -> None:
    """Avoid QMenu.exec() hang in plus-click e2e (PYPOST-1157)."""
    session.window.tabs._protocol_picker = lambda *_a, **_k: TabProtocol.HTTP


def _golden_fill_send_and_settle(session: AgentAppSession) -> None:
    """Fill URL/method, Send with canned OK, wait for status then body."""
    tab = session.current_request_tab()
    find_widget(tab, URL_INPUT)
    find_widget(tab, METHOD_COMBO)
    find_widget(tab, SEND_BUTTON)

    session.ui_fill(URL_INPUT, FIXTURE_URL, in_current_tab=True)
    session.ui_select(METHOD_COMBO, FIXTURE_METHOD, in_current_tab=True)

    with stub_agent_e2e_http(CANNED_GOLDEN_OK):
        session.ui_click(SEND_BUTTON, in_current_tab=True)
        wait_response_after_send(
            session,
            status_label=FIXTURE_STATUS_LABEL,
            body_text=FIXTURE_BODY_DISPLAY,
            step="wait_response_after_send",
            message_prefix="golden Send settle failed",
            in_current_tab=True,
        )

    assert CANNED_GOLDEN_OK.response.status_code == FIXTURE_STATUS


def test_agent_golden_request_response_flow(
    agent_e2e_session: AgentAppSession,
) -> None:
    """Compose lifecycle + identity + actions + text wait for Send → 200."""
    session = agent_e2e_session
    assert session.window.is_ui_ready is True
    _golden_fill_send_and_settle(session)


def test_agent_golden_plus_tab_create_when_no_blank_tab(
    qapp: QApplication,
    agent_e2e_session: AgentAppSession,
) -> None:
    """PYPOST-921: plus-tab create when restore left no blank request tab."""
    session = agent_e2e_session
    assert session.window.is_ui_ready is True
    _strip_request_tabs(session, qapp)

    _inject_http_protocol_picker(session)
    session.ui_click(PLUS_TAB_BUTTON)
    qapp.processEvents()
    assert isinstance(session.current_request_tab(), RequestTab)

    _golden_fill_send_and_settle(session)


def test_agent_golden_settle_timeout_includes_step_and_excerpt(
    agent_e2e_session: AgentAppSession,
) -> None:
    """PYPOST-950: forced text-wait settle timeout carries step + excerpt."""
    session = agent_e2e_session
    assert session.window.is_ui_ready is True
    session.ui_fill(URL_INPUT, FIXTURE_URL)
    session.ui_select(METHOD_COMBO, FIXTURE_METHOD)

    with stub_agent_e2e_http(CANNED_GOLDEN_OK):
        session.ui_click(SEND_BUTTON)
        with pytest.raises(UiWaitTimeoutError) as exc_info:
            try:
                session.wait_for_text(
                    RESPONSE_STATUS,
                    "Status: 999",
                    timeout=FORCED_SETTLE_TIMEOUT_S,
                    in_current_tab=True,
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

    diagnostics = exc_info.value.diagnostics
    assert diagnostics.get("step") == "wait_response_after_send"
    assert "response_excerpt" in diagnostics
    assert isinstance(diagnostics["response_excerpt"], str)
    assert diagnostics.get("widget_id") == RESPONSE_STATUS
    assert "expected" in diagnostics
