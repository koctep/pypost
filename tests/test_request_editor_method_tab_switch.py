import sys
import unittest
from PySide6.QtWidgets import QApplication

from pypost.models.models import RequestData
from pypost.ui.widgets.request_editor import RequestWidget

_app = None


def _get_app():
    global _app
    if _app is None:
        _app = QApplication.instance() or QApplication(sys.argv)
    return _app


class TestAutoSwitchToBodyTab(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _get_app()

    def setUp(self):
        self.widget = RequestWidget()

    def tearDown(self):
        self.widget.close()
        self.widget.deleteLater()

    # --- auto-switch cases ---

    def test_post_switches_to_body(self):
        self.widget.method_combo.setCurrentText("POST")
        self.assertIs(self.widget.detail_tabs.currentWidget(), self.widget.body_edit)

    def test_put_switches_to_body(self):
        self.widget.method_combo.setCurrentText("PUT")
        self.assertIs(self.widget.detail_tabs.currentWidget(), self.widget.body_edit)

    # --- no-switch cases ---

    def test_get_does_not_switch_to_body(self):
        self.widget.method_combo.setCurrentText("POST")        # switch to body
        self.widget.detail_tabs.setCurrentIndex(0)             # manually go to Params
        self.widget.method_combo.setCurrentText("GET")
        self.assertEqual(self.widget.detail_tabs.currentIndex(), 0)

    def test_delete_does_not_switch_to_body(self):
        self.widget.detail_tabs.setCurrentIndex(0)
        self.widget.method_combo.setCurrentText("DELETE")
        self.assertEqual(self.widget.detail_tabs.currentIndex(), 0)

    def test_patch_does_not_switch_to_body(self):
        self.widget.detail_tabs.setCurrentIndex(0)
        self.widget.method_combo.setCurrentText("PATCH")
        self.assertEqual(self.widget.detail_tabs.currentIndex(), 0)

    # --- load_data must NOT auto-switch ---

    def test_load_data_post_does_not_switch_tab(self):
        self.widget.detail_tabs.setCurrentIndex(0)
        self.widget.request_data = RequestData(method="POST")
        self.widget.load_data()
        self.assertEqual(self.widget.detail_tabs.currentIndex(), 0)

    def test_load_data_put_does_not_switch_tab(self):
        self.widget.detail_tabs.setCurrentIndex(1)
        self.widget.request_data = RequestData(method="PUT")
        self.widget.load_data()
        self.assertEqual(self.widget.detail_tabs.currentIndex(), 1)

    # --- guard flag ---

    def test_loading_flag_reset_after_load_data(self):
        self.widget.request_data = RequestData(method="POST")
        self.widget.load_data()
        self.assertFalse(self.widget._loading)


if __name__ == "__main__":
    unittest.main()
