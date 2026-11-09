"""Failing repro for PYPOST-1392 — reveal state across indent reformatting.

Desired behavior (fails on current code): after the user reveals a masked field and
JSON indent size changes, that field stays revealed and sibling masked fields stay
masked rather than resetting all spans to the default masked state.
"""

from __future__ import annotations

import json

import pytest
from PySide6.QtWidgets import QApplication

from pypost.models.models import RequestData
from pypost.models.response import ResponseData
from pypost.ui.widgets.response_view import ResponseView

pytestmark = pytest.mark.timeout(60)


def _span_by_path(view: ResponseView, path_substr: str):
    matches = [s for s in view.mask_controller.spans() if path_substr in s.path]
    assert len(matches) == 1, f"expected one span matching {path_substr!r}, got {matches}"
    return matches[0]


def test_reveal_state_preserved_across_indent_reformat(qapp: QApplication) -> None:
    """Revealed field must remain revealed after set_indent_size reformats the body."""
    view = ResponseView(indent_size=2)
    try:
        token_secret = "token_secret_abc"
        password_secret = "password_secret_xyz"
        req = RequestData(hidden_response_fields=["token", "password"])
        resp = ResponseData(
            status_code=200,
            headers={"Content-Type": "application/json"},
            body=json.dumps(
                {
                    "token": token_secret,
                    "password": password_secret,
                    "status": "ok",
                }
            ),
            elapsed_time=0.1,
            size=80,
        )
        view.display_response(resp, hidden_fields=req.hidden_response_fields)

        token_span = _span_by_path(view, "token")
        password_span = _span_by_path(view, "password")
        assert token_span.is_revealed is False
        assert password_span.is_revealed is False
        assert token_secret not in view.body_view.toPlainText()
        assert password_secret not in view.body_view.toPlainText()

        revealed = view.mask_controller.handle_click(token_span.start_pos + 1)
        assert revealed is True
        assert token_span.is_revealed is True
        assert token_secret in view.body_view.toPlainText()
        assert password_secret not in view.body_view.toPlainText()

        view.set_indent_size(4)

        token_after = _span_by_path(view, "token")
        password_after = _span_by_path(view, "password")
        assert token_after.is_revealed is True, (
            "token reveal state must survive indent reformat"
        )
        assert token_secret in view.body_view.toPlainText(), (
            "revealed token secret must remain visible after indent reformat"
        )
        assert password_after.is_revealed is False, (
            "unrevealed password must stay masked after indent reformat"
        )
        assert password_secret not in view.body_view.toPlainText(), (
            "password secret must not leak after indent reformat"
        )
        assert '"***"' in view.body_view.toPlainText()
    finally:
        view.close()


def test_reveal_state_resets_on_new_response(qapp: QApplication) -> None:
    """A different response must start fully masked (no stale reveals)."""
    view = ResponseView(indent_size=2)
    try:
        secret_a = "first_secret_value"
        resp_a = ResponseData(
            status_code=200,
            headers={"Content-Type": "application/json"},
            body=json.dumps({"token": secret_a, "status": "ok"}),
            elapsed_time=0.1,
            size=40,
        )
        view.display_response(resp_a, hidden_fields=["token"])
        span_a = _span_by_path(view, "token")
        assert view.mask_controller.handle_click(span_a.start_pos + 1) is True
        assert secret_a in view.body_view.toPlainText()

        secret_b = "second_secret_value"
        resp_b = ResponseData(
            status_code=200,
            headers={"Content-Type": "application/json"},
            body=json.dumps({"token": secret_b, "status": "ok"}),
            elapsed_time=0.1,
            size=40,
        )
        view.display_response(resp_b, hidden_fields=["token"])
        span_b = _span_by_path(view, "token")
        assert span_b.is_revealed is False
        assert secret_b not in view.body_view.toPlainText()
        assert '"***"' in view.body_view.toPlainText()
    finally:
        view.close()
