"""PYPOST-871 / PYPOST-898: Seed POST GUI Send uses shared HTTP stub + body.

Blank-session fill path (PYPOST-871) and optional collection-tree open
(PYPOST-898) both assert status/body under ``CANNED_SEED_POST_OK``.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from PySide6.QtWidgets import QTreeView

from pypost.agent import AgentAppSession, UiWaitTimeoutError, find_widget
from pypost.fixtures.agent_e2e_http import (
    CANNED_SEED_POST_OK,
    SEED_POST_OK_BODY,
    SEED_POST_RESOLVED_URL,
    stub_agent_e2e_http,
)
from pypost.fixtures.agent_e2e_seed import (
    SEED_POST_BODY,
    SEED_POST_REQUEST_NAME,
    SEED_POST_URL,
)
from pypost.ui.widget_ids import (
    COLLECTION_TREE,
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
from tests.helpers.agent_e2e_send_settle import (
    json_response_body_display,
    wait_response_after_send,
)
from tests.helpers.agent_e2e_tree import click_tree_row_by_text

pytestmark = [
    pytest.mark.timeout(60),
    pytest.mark.agent_e2e,
]

_STATUS_LABEL = "Status: 200"
_BODY_DISPLAY = json_response_body_display(SEED_POST_OK_BODY)
# Snapshot join still carries compact JSON from sanitize; post-settle only.
_BODY_IN_SNAPSHOT = json.dumps(json.loads(SEED_POST_OK_BODY), ensure_ascii=False)
_TREE_POST_LABEL = f"POST {SEED_POST_REQUEST_NAME}"


def _snapshot_value(snap: dict, widget_id: str) -> str | None:
    node = subtree_by_name(snap, widget_id)
    if node is None:
        return None
    value = node.get("value")
    return value if isinstance(value, str) else None


def _seed_post_editor_ready(snap: dict) -> bool:
    return (
        _snapshot_value(snap, METHOD_COMBO) == "POST"
        and _snapshot_value(snap, URL_INPUT) == SEED_POST_URL
        and SEED_POST_BODY in (_snapshot_value(snap, REQUEST_BODY_EDIT) or "")
    )


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
        wait_response_after_send(
            session,
            status_label=_STATUS_LABEL,
            body_text=_BODY_DISPLAY,
            step="wait_response_after_seed_post_send",
            message_prefix="seed POST Send settle failed",
        )
        snap = session.ui_snapshot()

    panel = subtree_by_name(snap, RESPONSE_PANEL)
    assert panel is not None
    joined = joined_panel_values(snap)
    assert _STATUS_LABEL in joined
    assert _BODY_IN_SNAPSHOT in joined
    assert stub_agent_e2e_http is agent_e2e_http_stub


def test_seed_post_open_from_collection_tree_then_send(
    seeded_agent_e2e_session: AgentAppSession,
    agent_e2e_http_stub: Any,
) -> None:
    """PYPOST-898: open Seed POST via tree, then Send under shared stub."""
    session = seeded_agent_e2e_session
    assert session.window.is_ui_ready is True
    tree = session.window.findChild(QTreeView, COLLECTION_TREE)
    assert tree is not None

    click_tree_row_by_text(tree, _TREE_POST_LABEL)
    try:
        session.wait_for_snapshot(
            _seed_post_editor_ready,
            timeout=10.0,
        )
    except UiWaitTimeoutError as exc:
        raise UiWaitTimeoutError(
            f"seed POST tree-open settle failed: {exc}",
            timeout_s=exc.timeout_s,
            condition=exc.condition,
            diagnostics={
                **exc.diagnostics,
                "step": "wait_seed_post_editor_from_tree",
            },
        ) from exc

    with agent_e2e_http_stub(CANNED_SEED_POST_OK):
        # Tree open adds a tab; window-scoped find hits the blank tab's Send.
        session.ui_click(SEND_BUTTON, in_current_tab=True)
        wait_response_after_send(
            session,
            status_label=_STATUS_LABEL,
            body_text=_BODY_DISPLAY,
            step="wait_response_after_seed_post_tree_send",
            message_prefix="seed POST tree Send settle failed",
            in_current_tab=True,
        )
        snap = session.ui_snapshot()

    joined = joined_panel_values(snap)
    assert _STATUS_LABEL in joined
    assert _BODY_IN_SNAPSHOT in joined
