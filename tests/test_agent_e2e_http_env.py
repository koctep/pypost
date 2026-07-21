"""PYPOST-859: Env-pack Send uses shared HTTP stub + seed URL."""

from __future__ import annotations

import json
from typing import Any

import pytest

from pypost.agent import AgentAppSession, UiWaitTimeoutError, find_widget
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

pytestmark = [
    pytest.mark.timeout(60),
    pytest.mark.agent_e2e,
]

_STATUS_LABEL = "Status: 200"
_BODY_IN_SNAPSHOT = json.dumps(
    json.loads(SEED_GET_OK_BODY), ensure_ascii=False
)
_SEND_SETTLE_TIMEOUT_S = 15.0


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


def _response_ready(snap: dict[str, Any]) -> bool:
    panel = _subtree_by_name(snap, RESPONSE_PANEL)
    if panel is None:
        return False
    joined = "\n".join(_walk_values(panel))
    return _STATUS_LABEL in joined and _BODY_IN_SNAPSHOT in joined


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
        try:
            snap = session.wait_for_snapshot(
                _response_ready,
                timeout=_SEND_SETTLE_TIMEOUT_S,
            )
        except UiWaitTimeoutError as exc:
            raise UiWaitTimeoutError(
                f"env seed Send settle failed: {exc}",
                timeout_s=exc.timeout_s,
                condition=exc.condition,
                diagnostics={
                    **exc.diagnostics,
                    "step": "wait_response_after_seed_send",
                },
            ) from exc

    panel = _subtree_by_name(snap, RESPONSE_PANEL)
    assert panel is not None
    joined = "\n".join(_walk_values(panel))
    assert _STATUS_LABEL in joined
    assert _BODY_IN_SNAPSHOT in joined
    # Catalog entry still importable for authors extending scenarios.
    assert stub_agent_e2e_http is agent_e2e_http_stub
