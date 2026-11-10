"""Red repro for PYPOST-1551.

A reveal choice for a field that left the applied spans is restored when
that field comes back. A field that stayed keeps its choice, including
across indent.
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


def test_field_that_left_starts_masked_when_it_returns(qapp: QApplication) -> None:
    """A field that left starts masked again; a field that stayed keeps its choice."""
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
        response = _response(body)
        hidden = ["token", "password", "session"]
        view.display_response(response, hidden_fields=hidden)

        text = view.body_view.toPlainText()
        assert _span_by_path(view, "token").is_revealed is False
        assert _span_by_path(view, "password").is_revealed is False
        assert _span_by_path(view, "session").is_revealed is False
        assert token_secret not in text
        assert password_secret not in text
        assert session_secret not in text

        token = _click(view, "token")
        assert token.is_revealed is True
        password = _click(view, "password")
        assert password.is_revealed is True
        session = _click(view, "session")
        assert session.is_revealed is True
        session = _click(view, "session")
        assert session.is_revealed is False
        text = view.body_view.toPlainText()
        assert token_secret in text
        assert password_secret in text
        assert session_secret not in text

        view.display_response(
            response,
            hidden_fields=["password", "session"],
            preserve_reveal_state=True,
        )
        text = view.body_view.toPlainText()
        assert _span_by_path(view, "password").is_revealed is True
        assert password_secret in text
        session = _span_by_path(view, "session")
        assert session.is_revealed is False
        assert session_secret not in text
        assert '"***"' in text
        paths = [span.path for span in view.mask_controller.spans()]
        assert all("token" not in path for path in paths)
        assert token_secret in text

        view.set_indent_size(4)
        text = view.body_view.toPlainText()
        assert text.startswith('{\n    "')
        assert _span_by_path(view, "password").is_revealed is True
        assert password_secret in text
        assert _span_by_path(view, "session").is_revealed is False
        assert session_secret not in text

        view.display_response(
            response,
            hidden_fields=hidden,
            preserve_reveal_state=True,
        )
        text = view.body_view.toPlainText()
        assert _span_by_path(view, "password").is_revealed is True
        assert password_secret in text
        assert _span_by_path(view, "session").is_revealed is False
        assert session_secret not in text
        returned = _span_by_path(view, "token")
        assert returned.is_revealed is False, (
            "token starts masked after it left the span set; "
            "stale reveal was restored"
        )
        assert token_secret not in text
        assert '"***"' in text
    finally:
        view.close()
