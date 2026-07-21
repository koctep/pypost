"""PYPOST-890: Agent e2e matrix — Send/response presentation invariants.

Parametrized method × request-body-shape cells drive the agent UI path with
deterministic streaming HTTP stubs. Each cell asserts desired presentation:

- unique stub body token appears exactly once under ``RESPONSE_PANEL``
- ``Status: {code}`` appears exactly once and matches the stub

Default HEAD (``_discard_chunk_buffer`` present) is expected green for smoke.
Red proof (do not commit): temporarily no-op ``_discard_chunk_buffer`` in
``_on_request_finished`` while keeping ``canned_send_with_one_chunk`` — at
least one streaming cell fails with body token count >= 2; then restore.

Smoke cells are ``agent_e2e`` only (default ``make test-agent-e2e``). Full
cartesian marks non-smoke params ``slow``. Non-200 smoke probe:
``POST×json_ok`` → stub status 201.

Sibling lock ``tests/test_agent_e2e_double_response_body.py`` is untouched.
Failing product cells → ``xfail`` + ``ai-tasks/PYPOST-890/findings.md``.
"""

from __future__ import annotations

from typing import Any

import pytest
from PySide6.QtCore import QCoreApplication
from PySide6.QtTest import QTest

from pypost.agent import AgentAppSession, UiWaitTimeoutError, find_widget
from pypost.fixtures.agent_e2e_http import (
    canned_send_with_one_chunk,
    make_canned_http_result,
    stub_agent_e2e_http,
)
from pypost.ui.widget_ids import (
    METHOD_COMBO,
    REQUEST_BODY_EDIT,
    REQUEST_DETAIL_TABS,
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

_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE")
_SHAPES = ("empty", "json_ok", "json_malformed", "text", "large")

# Smoke slice (architecture): plus POST×json_ok carries non-200 (201).
_SMOKE_CELLS = frozenset(
    {
        ("GET", "empty"),
        ("POST", "json_ok"),
        ("PUT", "json_malformed"),
        ("PATCH", "text"),
        ("DELETE", "empty"),
    }
)

# Methods that do not auto-switch detail_tabs to Body.
_NEEDS_BODY_TAB = frozenset({"GET", "PATCH", "DELETE"})

_BODY_TEXT: dict[str, str] = {
    "empty": "",
    "json_ok": '{"probe": true}',
    "json_malformed": '{ { "data": { } } }',
    "text": "not-json-probe",
    # ~8 KiB repeating ASCII (suite budget; omit only if documented in findings).
    "large": ("ABCDEFGHIJKLMNOP\n" * 512),
}


def _cell_url(method: str, shape: str) -> str:
    return f"https://example.test/pypost-890/{method.lower()}/{shape}"


def _cell_token(method: str, shape: str) -> str:
    return f"pypost-890-{method.lower()}-{shape}-once"


def _cell_status(method: str, shape: str) -> int:
    # Pin non-200 smoke probe on POST×json_ok (architecture).
    if method == "POST" and shape == "json_ok":
        return 201
    return 200


def _matrix_params() -> list[Any]:
    params: list[Any] = []
    for method in _METHODS:
        for shape in _SHAPES:
            marks: list[Any] = []
            if (method, shape) not in _SMOKE_CELLS:
                marks.append(pytest.mark.slow)
            params.append(
                pytest.param(
                    method,
                    shape,
                    id=f"{method}-{shape}",
                    marks=marks,
                )
            )
    return params


def _ensure_body_tab_visible(session: AgentAppSession) -> None:
    """Show Body tab so ``REQUEST_BODY_EDIT`` is interactable (GET/PATCH/DELETE).

    Uses ``REQUEST_DETAIL_TABS`` identity; selects the page that owns the body
    editor (no RequestWidget type walk).
    """
    tabs = find_widget(session.window, REQUEST_DETAIL_TABS)
    body = find_widget(session.window, REQUEST_BODY_EDIT)
    page: Any = body
    while page is not None:
        if tabs.indexOf(page) >= 0:
            tabs.setCurrentWidget(page)
            QCoreApplication.processEvents()
            return
        page = page.parentWidget()
    raise AssertionError(
        "REQUEST_BODY_EDIT not under REQUEST_DETAIL_TABS; cannot select Body"
    )


@pytest.mark.parametrize("method,body_shape", _matrix_params())
def test_agent_e2e_presentation_matrix_cell(
    agent_e2e_session: AgentAppSession,
    method: str,
    body_shape: str,
) -> None:
    """One method × body cell → stubbed Send → once-only body and status."""
    session = agent_e2e_session
    assert session.window.is_ui_ready is True
    find_widget(session.window, URL_INPUT)
    find_widget(session.window, METHOD_COMBO)
    find_widget(session.window, SEND_BUTTON)
    find_widget(session.window, REQUEST_BODY_EDIT)

    url = _cell_url(method, body_shape)
    token = _cell_token(method, body_shape)
    status = _cell_status(method, body_shape)
    status_label = f"Status: {status}"
    body_text = _BODY_TEXT[body_shape]
    cell_id = f"{method}-{body_shape}"

    session.ui_fill(URL_INPUT, url)
    session.ui_select(METHOD_COMBO, method)
    if body_shape != "empty":
        if method in _NEEDS_BODY_TAB:
            _ensure_body_tab_visible(session)
        session.ui_fill(REQUEST_BODY_EDIT, body_text)

    canned = make_canned_http_result(
        url=url,
        status_code=status,
        body=token,
        headers={"Content-Type": "text/plain"},
        resolved_body=body_text,
    )
    stub_name = f"presentation_matrix_{method.lower()}_{body_shape}"

    def _response_ready(snap: dict[str, Any]) -> bool:
        joined = joined_panel_values(snap)
        return status_label in joined and token in joined

    stub = canned_send_with_one_chunk(canned)
    with stub_agent_e2e_http(stub, name=stub_name):
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
                f"presentation matrix Send settle failed cell={cell_id}: "
                f"{exc}; response_excerpt={excerpt!r}",
                timeout_s=exc.timeout_s,
                condition=exc.condition,
                diagnostics={
                    **exc.diagnostics,
                    "step": "wait_response_after_send",
                    "cell": cell_id,
                    "response_excerpt": excerpt,
                },
            ) from exc
        QTest.qWait(_CHUNK_FLUSH_SETTLE_MS)
        snap = session.ui_snapshot()

    panel = subtree_by_name(snap, RESPONSE_PANEL)
    excerpt = response_panel_excerpt(snap)
    assert panel is not None, (
        f"RESPONSE_PANEL missing after Send cell={cell_id}; excerpt={excerpt!r}"
    )
    joined = joined_panel_values(snap)
    body_count = joined.count(token)
    status_count = joined.count(status_label)
    assert body_count == 1, (
        f"cell={cell_id}: expected body token {token!r} exactly once "
        f"(got count={body_count}; double-body regression if count>=2); "
        f"excerpt={excerpt!r}"
    )
    assert status_count == 1, (
        f"cell={cell_id}: expected {status_label!r} exactly once "
        f"(got count={status_count}); excerpt={excerpt!r}"
    )
