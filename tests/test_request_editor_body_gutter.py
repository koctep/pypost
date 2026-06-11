"""RequestWidget integration tests for Body tab line-number gutter (PYPOST-516)."""

import sys
import unittest

from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from pypost.ui.widgets.code_editor import CodeEditor
from pypost.ui.widgets.request_editor import RequestWidget

_app = None


def _get_app():
    global _app
    if _app is None:
        _app = QApplication.instance() or QApplication(sys.argv)
    return _app


class TestRequestWidgetBodyGutter(unittest.TestCase):
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

    def _switch_to_body_tab(self):
        self.widget.method_combo.setCurrentText("POST")
        self.assertIs(self.widget.detail_tabs.currentWidget(), self.widget.body_tab)

    def test_body_editor_is_code_editor_with_gutter(self):
        self._switch_to_body_tab()
        editor = self.widget.body_edit
        self.assertIsInstance(editor, CodeEditor)
        editor.setPlainText("line one\nline two")
        margin = editor.viewportMargins().left()
        self.assertGreater(margin, 0)
        self.assertEqual(margin, editor.line_number_area_width())

    def test_gutter_width_grows_with_line_count_in_widget_hierarchy(self):
        self._switch_to_body_tab()
        editor = self.widget.body_edit
        editor.setPlainText("\n".join(str(i) for i in range(1, 10)))
        width_nine = editor.line_number_area_width()
        editor.setPlainText("\n".join(str(i) for i in range(1, 11)))
        self.assertGreater(editor.line_number_area_width(), width_nine)
        self.assertEqual(
            editor.viewportMargins().left(),
            editor.line_number_area_width(),
        )

    def test_gutter_click_does_not_modify_body_in_widget_hierarchy(self):
        self._switch_to_body_tab()
        editor = self.widget.body_edit
        editor.setPlainText('{"a": 1}')
        before = editor.toPlainText()
        gutter_x = editor.viewportMargins().left() // 2
        QTest.mouseClick(
            editor._line_number_area,
            Qt.MouseButton.LeftButton,
            pos=QPoint(gutter_x, 5),
        )
        self.assertEqual(editor.toPlainText(), before)


if __name__ == "__main__":
    unittest.main()
