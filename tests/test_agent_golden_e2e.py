"""PYPOST-838: Golden e2e — agent completes one request/response product flow."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import patch

import pytest

from pypost.agent import AgentAppSession, UiWaitTimeoutError, find_widget
from pypost.core.http_client import HTTPRequestResult, ResolvedRequestFields
from pypost.models.response import ResponseData
from pypost.ui.widget_ids import (
    METHOD_COMBO,
    RESPONSE_PANEL,
    SEND_BUTTON,
    URL_INPUT,
)

pytestmark = [
    pytest.mark.timeout(60),
    pytest.mark.agent_e2e,
]

FIXTURE_URL = "https://example.test/agent-golden"
FIXTURE_METHOD = "GET"
FIXTURE_STATUS = 200
FIXTURE_BODY = '{"ok": true}'
# Snapshot sanitize_text re-dumps JSON without indent; assert that form.
FIXTURE_BODY_IN_SNAPSHOT = json.dumps(
    json.loads(FIXTURE_BODY), ensure_ascii=False
)
FIXTURE_STATUS_LABEL = f"Status: {FIXTURE_STATUS}"

_SEND_SETTLE_TIMEOUT_S = 15.0


def _canned_ok() -> HTTPRequestResult:
    return HTTPRequestResult(
        response=ResponseData(
            status_code=FIXTURE_STATUS,
            headers={"Content-Type": "application/json"},
            body=FIXTURE_BODY,
            elapsed_time=0.01,
            size=len(FIXTURE_BODY),
        ),
        resolved=ResolvedRequestFields(
            url=FIXTURE_URL, headers={}, body=""
        ),
    )


def _walk_values(node: dict[str, Any]) -> list[str]:
    values: list[str] = []
    raw = node.get("value")
    if isinstance(raw, str) and raw:
        values.append(raw)
    for child in node.get("children") or []:
        if isinstance(child, dict):
            values.extend(_walk_values(child))
    return values


def _subtree_by_name(node: dict[str, Any], name: str) -> dict[str, Any] | None:
    if node.get("name") == name:
        return node
    for child in node.get("children") or []:
        if isinstance(child, dict):
            found = _subtree_by_name(child, name)
            if found is not None:
                return found
    return None


def _response_panel_excerpt(snap: dict[str, Any]) -> str:
    panel = _subtree_by_name(snap, RESPONSE_PANEL)
    if panel is None:
        return "<response panel not in snapshot>"
    joined = " | ".join(_walk_values(panel))
    if len(joined) > 400:
        return joined[:400] + "…"
    return joined or "<response panel has no values>"


def _response_ready(snap: dict[str, Any]) -> bool:
    panel = _subtree_by_name(snap, RESPONSE_PANEL)
    if panel is None:
        return False
    joined = "\n".join(_walk_values(panel))
    return (
        FIXTURE_STATUS_LABEL in joined
        and FIXTURE_BODY_IN_SNAPSHOT in joined
    )


def _assert_response_ui(snap: dict[str, Any]) -> None:
    panel = _subtree_by_name(snap, RESPONSE_PANEL)
    excerpt = _response_panel_excerpt(snap)
    assert panel is not None, (
        f"RESPONSE_PANEL missing after Send; excerpt={excerpt!r}"
    )
    joined = "\n".join(_walk_values(panel))
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

    with patch(
        "pypost.core.request_service.HTTPClient.send_request",
        return_value=_canned_ok(),
    ):
        session.ui_click(SEND_BUTTON)
        try:
            snap = session.wait_for_snapshot(
                _response_ready,
                timeout=_SEND_SETTLE_TIMEOUT_S,
            )
        except UiWaitTimeoutError as exc:
            last = session.ui_snapshot()
            excerpt = _response_panel_excerpt(last)
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
