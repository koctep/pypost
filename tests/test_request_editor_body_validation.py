"""RequestWidget integration tests for Body tab validation banner (PYPOST-521)."""

import sys
import unittest

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from pypost.ui.widgets.request_editor import RequestWidget

_app = None


def _get_app():
    global _app
    if _app is None:
        _app = QApplication.instance() or QApplication(sys.argv)
    return _app


class TestRequestWidgetBodyValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _get_app()

    def setUp(self):
        self.widget = RequestWidget()
        self.widget.show()
        QTest.qWaitForWindowExposed(self.widget)

    def tearDown(self):
        self.widget.close()
        self.widget.deleteLater()

    def test_invalid_json_shows_validation_banner_on_body_tab(self):
        self.widget.method_combo.setCurrentText("POST")
        self.assertIs(self.widget.detail_tabs.currentWidget(), self.widget.body_tab)
        self.widget.body_edit.setPlainText("{bad")
        self.widget.body_edit.validation_controller()._run_validate()

        errors = self.widget.body_edit.validation_controller().errors()
        self.assertEqual(len(errors), 1)
        label = self.widget.body_edit.validation_controller()._error_label
        self.assertIn("Line 1", label.text())


if __name__ == "__main__":
    unittest.main()
