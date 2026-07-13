"""Qt-level tests for ResponseView search bar (PYPOST-365, PYPOST-37, PYPOST-363)."""

import pytest

pytestmark = pytest.mark.timeout(60)

from unittest.mock import MagicMock

from PySide6.QtTest import QTest

from pypost.models.response import ResponseData
from pypost.ui.widgets.response_view import SEARCH_DEBOUNCE_MS, ResponseView


class TestResponseViewSearch:
    def test_empty_query_clears_status(self, qapp):
        view = ResponseView()
        try:
            view.body_view.setPlainText("hello world")
            view.search_input.setText("hello")
            view._on_search_text_changed()
            assert view.search_status_label.text() != ""
            view.search_input.clear()
            view._on_search_text_changed()
            assert view.search_status_label.text() == ""
        finally:
            view.close()

    def test_typed_search_shows_match_counter(self, qapp):
        view = ResponseView()
        try:
            view.body_view.setPlainText("alpha beta alpha gamma alpha")
            view.search_input.setText("alpha")
            view._on_search_text_changed()
            assert view.search_status_label.text() == "1 of 3"
        finally:
            view.close()

    def test_no_matches_shows_message(self, qapp):
        view = ResponseView()
        try:
            view.body_view.setPlainText("hello world")
            view.search_input.setText("missing")
            view._on_search_text_changed()
            assert view.search_status_label.text() == "No matches"
        finally:
            view.close()

    def test_find_next_advances_counter(self, qapp):
        view = ResponseView()
        try:
            view.body_view.setPlainText("foo bar foo baz foo")
            view.search_input.setText("foo")
            view._on_search_text_changed()
            assert view.search_status_label.text() == "1 of 3"
            view._find_next(source="next")
            assert view.search_status_label.text() == "2 of 3"
            view._find_next(source="next")
            assert view.search_status_label.text() == "3 of 3"
        finally:
            view.close()

    def test_find_previous_moves_backward(self, qapp):
        view = ResponseView()
        try:
            view.body_view.setPlainText("foo bar foo baz foo")
            view.search_input.setText("foo")
            view._on_search_text_changed()
            view._find_next(source="next")
            view._find_next(source="next")
            assert view.search_status_label.text() == "3 of 3"
            view._find_previous(source="previous")
            assert view.search_status_label.text() == "2 of 3"
        finally:
            view.close()

    def test_match_case_checkbox(self, qapp):
        view = ResponseView()
        try:
            view.body_view.setPlainText("Hello hello HELLO")
            view.search_input.setText("hello")
            view._on_search_text_changed()
            assert view.search_status_label.text() == "1 of 3"
            view.search_case_cb.setChecked(True)
            view._on_search_text_changed()
            assert view.search_status_label.text() == "1 of 1"
        finally:
            view.close()

    def test_metrics_tracked_on_typed_search(self, qapp):
        metrics = MagicMock()
        view = ResponseView(metrics=metrics)
        try:
            view.body_view.setPlainText("needle haystack needle")
            view.search_input.setText("needle")
            view._on_search_text_changed()
            metrics.track_gui_response_search_action.assert_called_with(
                source="typed", has_matches=True
            )
        finally:
            view.close()

    def test_large_document_shows_capped_match_counter(self, qapp):
        view = ResponseView()
        try:
            chunk = "hit" + ("x" * 50)
            body = chunk * 2500
            assert len(body) > 100 * 1024
            view.body_view.setPlainText(body)
            view.search_input.setText("hit")
            view._on_search_text_changed()
            assert view.search_status_label.text() == "1 of 1000+"
        finally:
            view.close()

    def test_large_document_exact_count_when_below_cap(self, qapp):
        view = ResponseView()
        try:
            body = ("z" * (100 * 1024 + 1)) + "foo bar foo baz foo"
            view.body_view.setPlainText(body)
            view.search_input.setText("foo")
            view._on_search_text_changed()
            assert view.search_status_label.text() == "1 of 3"
        finally:
            view.close()

    def test_display_response_clears_search(self, qapp):
        view = ResponseView()
        try:
            view.body_view.setPlainText("old content")
            view.search_input.setText("old")
            view._on_search_text_changed()
            response = ResponseData(
                status_code=200,
                headers={},
                body='{"ok": true}',
                elapsed_time=0.1,
                size=12,
            )
            view.display_response(response)
            assert view.search_input.text() == ""
            assert view.search_status_label.text() == ""
        finally:
            view.close()

    def test_display_response_pretty_prints_small_json(self, qapp):
        view = ResponseView(indent_size=2)
        try:
            response = ResponseData(
                status_code=200,
                headers={},
                body='{"ok":true}',
                elapsed_time=0.1,
                size=11,
            )
            view.display_response(response)
            text = view.body_view.toPlainText()
            assert "\n" in text
            assert '"ok"' in text
        finally:
            view.close()

    def test_display_response_skips_pretty_print_for_large_body(self, qapp):
        view = ResponseView(indent_size=2)
        try:
            body = '{"data":"' + ("x" * (100 * 1024 + 1)) + '"}'
            response = ResponseData(
                status_code=200,
                headers={},
                body=body,
                elapsed_time=0.1,
                size=len(body.encode("utf-8")),
            )
            view.display_response(response)
            assert view.body_view.toPlainText() == body
        finally:
            view.close()

    def test_small_document_searches_immediately(self, qapp):
        view = ResponseView()
        try:
            view.body_view.setPlainText("alpha beta alpha")
            view.search_input.setText("alpha")
            assert view.search_status_label.text() == "1 of 2"
        finally:
            view.close()

    def test_large_document_debounces_search(self, qapp):
        view = ResponseView()
        try:
            body = ("z" * (100 * 1024 + 1)) + "foo bar foo baz foo"
            view.body_view.setPlainText(body)
            view.search_input.setText("f")
            assert view.search_status_label.text() == ""
            view.search_input.setText("foo")
            assert view.search_status_label.text() == ""
            QTest.qWait(SEARCH_DEBOUNCE_MS + 50)
            assert view.search_status_label.text() == "1 of 3"
        finally:
            view.close()

    def test_large_document_clear_is_immediate(self, qapp):
        view = ResponseView()
        try:
            body = ("z" * (100 * 1024 + 1)) + "foo bar foo baz foo"
            view.body_view.setPlainText(body)
            view.search_input.setText("foo")
            QTest.qWait(SEARCH_DEBOUNCE_MS + 50)
            assert view.search_status_label.text() == "1 of 3"
            view.search_input.clear()
            assert view.search_status_label.text() == ""
        finally:
            view.close()
