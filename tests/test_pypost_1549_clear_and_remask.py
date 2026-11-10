"""Characterization for PYPOST-1549. Behavior already holds.

Clearing the response body forgets a reveal, so the next body starts masked
even when its text matches the cleared body. Masking a revealed value again,
then changing indent, leaves that value hidden. A value left revealed stays
visible, and a value never revealed stays masked.
"""

from __future__ import annotations

import json

import pytest
from PySide6.QtWidgets import QApplication

from pypost.models.response import ResponseData
from pypost.ui.widgets.response_view import ResponseView

pytestmark = pytest.mark.timeout(60)


def _span_by_path(view: ResponseView, path_substr: str):
    matches = [s for s in view.mask_controller.spans() if path_substr in s.path]
    assert len(matches) == 1, f"expected one span matching {path_substr!r}, got {matches}"
    return matches[0]


def _response(body: str) -> ResponseData:
    return ResponseData(
        status_code=200,
        headers={"Content-Type": "application/json"},
        body=body,
        elapsed_time=0.1,
        size=len(body),
    )


def _click(view: ResponseView, path_substr: str):
    span = _span_by_path(view, path_substr)
    assert view.mask_controller.handle_click(span.start_pos + 1) is True
    return span


def test_clear_body_forgets_reveal_for_matching_body(qapp: QApplication) -> None:
    """A cleared reveal stays forgotten when the next body text matches."""
    view = ResponseView(indent_size=2)
    try:
        token_secret = "token_secret_abc"
        password_secret = "password_secret_xyz"
        body = json.dumps(
            {"token": token_secret, "password": password_secret, "status": "ok"}
        )
        hidden = ["token", "password"]
        view.display_response(_response(body), hidden_fields=hidden)
        token = _click(view, "token")
        assert token.is_revealed is True
        assert token_secret in view.body_view.toPlainText()
        assert password_secret not in view.body_view.toPlainText()

        view.clear_body()
        view.display_response(_response(body), hidden_fields=hidden)

        text = view.body_view.toPlainText()
        assert _span_by_path(view, "token").is_revealed is False
        assert _span_by_path(view, "password").is_revealed is False
        assert token_secret not in text
        assert password_secret not in text
        assert '"***"' in text
    finally:
        view.close()


def test_remask_stays_hidden_across_indent_reformat(qapp: QApplication) -> None:
    """Re-mask stays hidden across indent; a left reveal stays visible."""
    view = ResponseView(indent_size=2)
    try:
        token_secret = "token_secret_abc"
        password_secret = "password_secret_xyz"
        session_secret = "session_secret_qrs"
        body = json.dumps(
            {
                "token": token_secret,
                "password": password_secret,
                "session": session_secret,
                "status": "ok",
            }
        )
        view.display_response(
            _response(body), hidden_fields=["token", "password", "session"]
        )
        token = _click(view, "token")
        assert token.is_revealed is True
        assert token_secret in view.body_view.toPlainText()
        token = _click(view, "token")
        assert token.is_revealed is False
        assert token_secret not in view.body_view.toPlainText()
        password = _click(view, "password")
        assert password.is_revealed is True
        assert password_secret in view.body_view.toPlainText()
        assert session_secret not in view.body_view.toPlainText()

        view.set_indent_size(4)

        text = view.body_view.toPlainText()
        assert _span_by_path(view, "token").is_revealed is False, "token stays hidden"
        assert token_secret not in text, "re-masked token secret stays covered"
        assert _span_by_path(view, "password").is_revealed is True, "password stays visible"
        assert password_secret in text, "revealed password secret stays visible"
        assert _span_by_path(view, "session").is_revealed is False, "session stays masked"
        assert session_secret not in text, "never-revealed session secret stays covered"
        assert '"***"' in text
    finally:
        view.close()
