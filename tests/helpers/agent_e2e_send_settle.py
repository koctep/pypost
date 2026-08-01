"""Shared Send settle helpers for agent e2e (PYPOST-948)."""

from __future__ import annotations

import json
from typing import Any

from pypost.agent import AgentAppSession, UiWaitTimeoutError
from pypost.ui.widget_ids import RESPONSE_BODY, RESPONSE_STATUS
from tests.helpers.agent_e2e_response_panel import response_panel_excerpt
from tests.helpers.agent_e2e_send import SEND_SETTLE_TIMEOUT_S

__all__ = [
    "json_response_body_display",
    "wait_response_after_send",
]


def json_response_body_display(raw: str) -> str:
    """Pretty-print JSON body text as shown in ``RESPONSE_BODY``."""
    return json.dumps(json.loads(raw), indent=2)


def wait_response_after_send(
    session: AgentAppSession,
    *,
    status_label: str,
    body_text: str,
    step: str,
    timeout: float = SEND_SETTLE_TIMEOUT_S,
    message_prefix: str = "Send settle failed",
    diagnostics_extra: dict[str, Any] | None = None,
    in_current_tab: bool = False,
) -> None:
    """Wait for status then body on ``RESPONSE_STATUS`` / ``RESPONSE_BODY``."""
    try:
        session.wait_for_text(
            RESPONSE_STATUS,
            status_label,
            timeout=timeout,
            in_current_tab=in_current_tab,
        )
        session.wait_for_text(
            RESPONSE_BODY,
            body_text,
            timeout=timeout,
            in_current_tab=in_current_tab,
        )
    except UiWaitTimeoutError as exc:
        excerpt = response_panel_excerpt(session.ui_snapshot())
        raise UiWaitTimeoutError(
            f"{message_prefix}: {exc}; response_excerpt={excerpt!r}",
            timeout_s=exc.timeout_s,
            condition=exc.condition,
            diagnostics={
                **exc.diagnostics,
                "step": step,
                "response_excerpt": excerpt,
                **(diagnostics_extra or {}),
            },
        ) from exc
