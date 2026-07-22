"""Integration tests for RequestTab → ResponseView search flow (PYPOST-357)."""

import pytest

pytestmark = pytest.mark.timeout(60)

import unittest
from unittest.mock import MagicMock

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from pypost.models.response import ResponseData
from pypost.models.settings import AppSettings
from pypost.ui.presenters.tabs_presenter import RequestTab, TabsPresenter

from tests.test_tabs_presenter import FakeRequestManager, FakeStateManager

def _response_body(text: str) -> ResponseData:
    encoded = text.encode("utf-8")
    return ResponseData(
        status_code=200,
        headers={},
        body=text,
        elapsed_time=0.05,
        size=len(encoded),
    )

@pytest.mark.usefixtures("qapp")

class TestResponseSearchFlowIntegration(unittest.TestCase):
    """GUI wiring: display response → type search → navigate → match counter."""

    def _active_tab(self, presenter: TabsPresenter) -> RequestTab:
        tab = presenter.widget.currentWidget()
        self.assertIsInstance(tab, RequestTab)
        return tab

    def _make_tab_with_response(self, body: str) -> RequestTab:
        rm = FakeRequestManager()
        sm = FakeStateManager()
        presenter = TabsPresenter(rm, sm, AppSettings(), metrics=MagicMock())
        presenter.add_new_tab(save_state=False)
        tab = self._active_tab(presenter)
        tab.response_view.display_response(_response_body(body))
        return tab

    def test_type_and_next_button_updates_match_counter(self):
        tab = self._make_tab_with_response("foo bar foo baz foo")
        rv = tab.response_view
        try:
            rv.search_input.setFocus()
            QTest.keyClicks(rv.search_input, "foo")
            self.assertEqual(rv.search_status_label.text(), "1 of 3")
            QTest.mouseClick(rv.search_next_btn, Qt.MouseButton.LeftButton)
            self.assertEqual(rv.search_status_label.text(), "2 of 3")
            QTest.mouseClick(rv.search_next_btn, Qt.MouseButton.LeftButton)
            self.assertEqual(rv.search_status_label.text(), "3 of 3")
        finally:
            tab.close()

    def test_enter_key_finds_next_match(self):
        tab = self._make_tab_with_response("alpha beta alpha gamma alpha")
        rv = tab.response_view
        try:
            rv.search_input.setText("alpha")
            self.assertEqual(rv.search_status_label.text(), "1 of 3")
            rv.search_input.setFocus()
            QTest.keyClick(rv.search_input, Qt.Key.Key_Return)
            self.assertEqual(rv.search_status_label.text(), "2 of 3")
        finally:
            tab.close()

    def test_typed_query_with_no_matches(self):
        tab = self._make_tab_with_response("hello world")
        rv = tab.response_view
        try:
            rv.search_input.setText("missing")
            self.assertEqual(rv.search_status_label.text(), "No matches")
        finally:
            tab.close()

    def test_new_response_clears_search_via_display_response(self):
        tab = self._make_tab_with_response("old content old")
        rv = tab.response_view
        try:
            rv.search_input.setText("old")
            self.assertEqual(rv.search_status_label.text(), "1 of 2")
            rv.display_response(_response_body('{"fresh": true}'))
            self.assertEqual(rv.search_input.text(), "")
            self.assertEqual(rv.search_status_label.text(), "")
        finally:
            tab.close()

if __name__ == "__main__":
    unittest.main()
