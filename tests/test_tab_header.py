import pytest

pytestmark = pytest.mark.timeout(60)

import unittest

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QTabBar, QTabWidget, QWidget

from pypost.ui.widgets.tab_header import PLUS_TAB_MARKER, RequestTabHeader


class TestRequestTabHeader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _make_header(self) -> tuple[RequestTabHeader, QTabWidget]:
        tabs = QTabWidget()
        header = RequestTabHeader()
        header.attach(tabs)
        return header, tabs

    def test_attach_installs_plus_tab_last(self):
        header, tabs = self._make_header()
        plus_idx = header.plus_tab_index()
        self.assertGreaterEqual(plus_idx, 0)
        self.assertEqual(plus_idx, tabs.count() - 1)

    def test_plus_tab_click_emits_new_tab_requested(self):
        header, _tabs = self._make_header()
        received = []
        header.new_tab_requested.connect(lambda: received.append(True))
        plus_idx = header.plus_tab_index()
        plus_btn = header.tab_bar.tabButton(plus_idx, QTabBar.ButtonPosition.LeftSide)
        QTest.mouseClick(plus_btn, Qt.MouseButton.LeftButton)
        self.assertEqual(received, [True])

    def test_plus_tab_tab_bar_clicked_emits_new_tab_requested(self):
        """Fallback path: chrome click outside embedded + button."""
        header, _tabs = self._make_header()
        received = []
        header.new_tab_requested.connect(lambda: received.append(True))
        plus_idx = header.plus_tab_index()
        header.tab_bar.tabBarClicked.emit(plus_idx)
        self.assertEqual(received, [True])

    def test_non_plus_tab_bar_clicked_does_not_emit_new_tab(self):
        header, tabs = self._make_header()
        plus_idx = header.plus_tab_index()
        tabs.insertTab(plus_idx, QWidget(), "Request")
        received = []
        header.new_tab_requested.connect(lambda: received.append(True))
        header.tab_bar.tabBarClicked.emit(0)
        self.assertEqual(received, [])

    def test_is_plus_tab_index(self):
        header, tabs = self._make_header()
        plus_idx = header.plus_tab_index()
        tabs.insertTab(plus_idx, QWidget(), "Request")
        self.assertTrue(header.is_plus_tab_index(header.plus_tab_index()))
        self.assertFalse(header.is_plus_tab_index(0))

    def test_navigable_tab_indices_skip_plus_tab(self):
        header, tabs = self._make_header()
        plus_idx = header.plus_tab_index()
        tabs.insertTab(plus_idx, QWidget(), "Request")
        navigable = header.navigable_tab_indices()
        self.assertNotIn(header.plus_tab_index(), navigable)
        self.assertIn(0, navigable)

    def test_set_tab_label_updates_text(self):
        header, tabs = self._make_header()
        plus_idx = header.plus_tab_index()
        tabs.insertTab(plus_idx, QWidget(), "Old")
        header.set_tab_label(0, "Renamed")
        self.assertEqual(tabs.tabText(0), "Renamed")

    def test_plus_tab_marker_constant(self):
        self.assertEqual(PLUS_TAB_MARKER, "pypost_plus_tab")


if __name__ == "__main__":
    unittest.main()
