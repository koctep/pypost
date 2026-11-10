"""Characterization for PYPOST-1550. Behavior already holds.

A longer response formats in the background. Revealing one value and
leaving another hidden, then changing indent, keeps those choices when
the background format is applied. A stale background result that
finishes after a newer display leaves that display and its choices.
"""

from __future__ import annotations

import json

import pytest
from PySide6.QtWidgets import QApplication

from pypost.models.response import ResponseData
from pypost.ui.widgets.response_mask_controller import MaskedTokenSpan
from pypost.ui.widgets.response_view import (
    LARGE_DOC_CHAR_THRESHOLD,
    MEDIUM_DOC_CHAR_THRESHOLD,
    ResponseView,
)
from tests.helpers.process_until import process_until

pytestmark = pytest.mark.timeout(60)

_HIDDEN = ["token", "password"]
_TOKEN = "token_secret_abc"
_PASSWORD = "password_secret_xyz"
_MARKER = "STALE_FORMAT_MARKER"


def _span(view: ResponseView, name: str) -> MaskedTokenSpan:
    matches = [span for span in view.mask_controller.spans() if span.path == name]
    assert len(matches) == 1, f"expected one span for {name!r}, got {matches}"
    return matches[0]


def _response(body: str, status: int = 200) -> ResponseData:
    return ResponseData(
        status_code=status,
        headers={"Content-Type": "application/json"},
        body=body,
        elapsed_time=0.1,
        size=len(body),
    )


def _medium_body(token: str, password: str) -> str:
    body = json.dumps(
        {"token": token, "password": password, "pad": "x" * MEDIUM_DOC_CHAR_THRESHOLD}
    )
    assert MEDIUM_DOC_CHAR_THRESHOLD <= len(body) <= LARGE_DOC_CHAR_THRESHOLD
    return body


def _wait_masked(view: ResponseView) -> None:
    process_until(
        lambda: view._mask_worker is None and len(view.mask_controller.spans()) >= 2,
        timeout_ms=10_000,
    )


def test_medium_indent_keeps_reveal_choices(qapp: QApplication) -> None:
    """Revealed token stays visible and hidden password stays masked."""
    view = ResponseView(indent_size=2)
    try:
        view.display_response(
            _response(_medium_body(_TOKEN, _PASSWORD)),
            hidden_fields=_HIDDEN,
        )
        _wait_masked(view)
        token = _span(view, "token")
        assert token.is_revealed is False
        assert view.mask_controller.handle_click(token.start_pos + 1) is True
        assert _PASSWORD not in view.body_view.toPlainText()

        view.set_indent_size(4)
        _wait_masked(view)

        text = view.body_view.toPlainText()
        assert text.startswith('{\n    "')
        assert _span(view, "token").is_revealed is True
        assert _TOKEN in text
        assert _span(view, "password").is_revealed is False
        assert _PASSWORD not in text
        assert '"***"' in text
    finally:
        view.close()


def test_stale_background_result_leaves_newer_display(qapp: QApplication) -> None:
    """A late older generation does not replace the newer display."""
    view = ResponseView(indent_size=2)
    try:
        view.display_response(
            _response(_medium_body("old_token_secret", "old_password_secret")),
            hidden_fields=_HIDDEN,
        )
        worker = view._mask_worker
        generation = view._mask_format_generation
        assert worker is not None

        newer_token = "newer_token_secret"
        newer_password = "newer_password_secret"
        short = json.dumps(
            {"token": newer_token, "password": newer_password, "status": "ok"}
        )
        assert len(short) < MEDIUM_DOC_CHAR_THRESHOLD
        view.display_response(_response(short, status=201), hidden_fields=_HIDDEN)
        assert view._mask_format_generation != generation
        token = _span(view, "token")
        assert view.mask_controller.handle_click(token.start_pos + 1) is True

        status = view.status_label.text()
        text = view.body_view.toPlainText()
        token_revealed = _span(view, "token").is_revealed
        password_revealed = _span(view, "password").is_revealed
        assert _MARKER not in text
        assert token_revealed is True
        assert password_revealed is False
        view._on_mask_formatting_completed(generation, _MARKER, [])
        assert worker.wait(10_000)

        assert view.status_label.text() == status
        assert view.body_view.toPlainText() == text
        assert _span(view, "token").is_revealed is token_revealed
        assert _span(view, "password").is_revealed is password_revealed
        assert newer_token in text
        assert newer_password not in text
        assert _MARKER not in view.body_view.toPlainText()
    finally:
        view.close()
