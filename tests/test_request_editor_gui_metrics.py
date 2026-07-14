"""RequestWidget GUI action metrics — Prometheus registry inspection (PYPOST-170)."""

import pytest

pytestmark = pytest.mark.timeout(60)

import sys
import unittest

from prometheus_client import generate_latest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from pypost.core.qt.metrics import MetricsManager
from pypost.ui.widgets.request_editor import RequestWidget


def _scrape(mm: MetricsManager) -> str:
    return generate_latest(mm.registry).decode("utf-8")


class TestRequestWidgetGuiActionMetrics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def setUp(self):
        self.metrics = MetricsManager()
        self.widget = RequestWidget(metrics=self.metrics)
        QTest.qWaitForWindowExposed(self.widget)

    def tearDown(self):
        self.widget.close()
        self.widget.deleteLater()

    def test_send_button_click_increments_gui_send_clicks_total(self):
        QTest.mouseClick(self.widget.send_btn, Qt.MouseButton.LeftButton)
        out = _scrape(self.metrics)
        self.assertIn("gui_send_clicks_total 1.0", out)

    def test_multiple_send_clicks_accumulate(self):
        QTest.mouseClick(self.widget.send_btn, Qt.MouseButton.LeftButton)
        QTest.mouseClick(self.widget.send_btn, Qt.MouseButton.LeftButton)
        out = _scrape(self.metrics)
        self.assertIn("gui_send_clicks_total 2.0", out)

    def test_save_menu_action_increments_labeled_save_counter(self):
        self.widget.handle_save_menu_action()
        out = _scrape(self.metrics)
        self.assertIn('gui_save_actions_total{source="menu"} 1.0', out)

    def test_save_shortcut_increments_labeled_save_counter(self):
        self.widget.handle_save_request_shortcut()
        out = _scrape(self.metrics)
        self.assertIn('gui_save_actions_total{source="shortcut"} 1.0', out)

    def test_save_as_menu_action_increments_save_as_counter(self):
        self.widget.handle_save_as_menu_action()
        out = _scrape(self.metrics)
        self.assertIn('gui_save_as_actions_total{source="menu"} 1.0', out)

    def test_save_as_shortcut_increments_save_as_counter(self):
        self.widget.handle_save_as_shortcut()
        out = _scrape(self.metrics)
        self.assertIn('gui_save_as_actions_total{source="shortcut"} 1.0', out)

    def test_copy_curl_menu_action_increments_copy_curl_counter(self):
        self.widget.handle_copy_curl_menu_action()
        out = _scrape(self.metrics)
        self.assertIn("gui_copy_curl_actions_total 1.0", out)


if __name__ == "__main__":
    unittest.main()
