"""Regression for response body display after streaming chunks (PYPOST-887).

Covers the chunk-flush vs display_response race: `_on_chunk_received` arms a
33ms flush timer; without discard, a late `_flush_chunk_buffer` would
`append_body` after `display_response` (`setText`) and show the body twice.
"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtTest import QTest

from pypost.models.response import ResponseData
from pypost.models.settings import AppSettings
from pypost.ui.presenters.tabs_presenter import TabsPresenter
from tests.test_tabs_presenter import (
    FakeRequestManager,
    FakeStateManager,
    _make_request,
)

pytestmark = pytest.mark.timeout(60)

# Non-JSON so display_response does not pretty-print (stable equality assert).
_BODY = "plain-response-body-not-json"


@pytest.fixture
def presenter_with_tab(qapp):
    rm = FakeRequestManager()
    sm = FakeStateManager()
    presenter = TabsPresenter(rm, sm, AppSettings(), metrics=MagicMock())
    req = _make_request("r1", "Test", "PUT")
    presenter.add_new_tab(req)
    tab = presenter.widget.widget(0)
    return presenter, tab


def _response(body: str) -> ResponseData:
    return ResponseData(
        status_code=200,
        headers={"Content-Type": "text/plain"},
        body=body,
        elapsed_time=0.05,
        size=len(body.encode("utf-8")),
    )


def _finish_after_chunk_then_flush(presenter: TabsPresenter, tab, body: str) -> str:
    """Chunk → finish (setText) → wait past flush timer → return body text.

    PYPOST-887: pending `_flush_chunk_buffer` must not append after
    `display_response`.
    """
    presenter._on_chunk_received(tab, body)
    presenter._on_request_finished(tab, _response(body))
    QTest.qWait(presenter._chunk_flush_ms + 50)
    return tab.response_view.body_view.toPlainText()


def test_response_body_shown_once_after_chunk_then_finish(presenter_with_tab) -> None:
    """Body shown once when finish races a pending chunk flush."""
    presenter, tab = presenter_with_tab
    text = _finish_after_chunk_then_flush(presenter, tab, _BODY)
    assert text == _BODY
    assert id(tab) not in presenter._chunk_buffers
    assert id(tab) not in presenter._chunk_flush_timers


def test_response_body_shown_once_for_get_not_put_only(presenter_with_tab) -> None:
    """Same race is not PUT-only (companion breadth case for PYPOST-887)."""
    presenter, tab = presenter_with_tab
    tab.request_data.method = "GET"
    text = _finish_after_chunk_then_flush(presenter, tab, _BODY)
    assert text == _BODY


def test_stream_flush_before_finish_still_shows_body_once(presenter_with_tab) -> None:
    """Mid-request flush remains; final display_response replaces with one body."""
    presenter, tab = presenter_with_tab
    presenter._on_chunk_received(tab, _BODY)
    QTest.qWait(presenter._chunk_flush_ms + 50)
    assert tab.response_view.body_view.toPlainText() == _BODY
    presenter._on_request_finished(tab, _response(_BODY))
    assert tab.response_view.body_view.toPlainText() == _BODY


def test_error_discards_pending_chunk_flush(presenter_with_tab, caplog) -> None:
    """Error path must cancel pending flush so late append cannot run."""
    presenter, tab = presenter_with_tab
    tab.response_view.clear_body()
    presenter._on_chunk_received(tab, _BODY)
    logger_name = "pypost.ui.presenters.tabs_presenter_worker"
    with (
        patch(
            "pypost.ui.presenters.tabs_presenter_worker.show_request_failed_error",
        ),
        caplog.at_level(logging.ERROR, logger=logger_name),
    ):
        presenter._on_request_error(tab, "connection refused")
    assert any("request_error" in r.message for r in caplog.records)
    QTest.qWait(presenter._chunk_flush_ms + 50)
    assert tab.response_view.body_view.toPlainText() == ""
    assert id(tab) not in presenter._chunk_buffers
    assert id(tab) not in presenter._chunk_flush_timers
