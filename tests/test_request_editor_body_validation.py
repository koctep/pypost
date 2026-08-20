"""RequestWidget integration tests for Body tab validation banner (PYPOST-521)."""

import pytest

import unittest

from PySide6.QtTest import QTest

from pypost.ui.widgets.request_editor import RequestWidget

pytestmark = pytest.mark.timeout(60)


@pytest.mark.usefixtures("qapp")

class TestRequestWidgetBodyValidation(unittest.TestCase):
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
