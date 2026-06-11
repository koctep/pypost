"""CodeEditor format validation tests (PYPOST-512)."""

import json
import unittest

from PySide6.QtGui import QTextDocument
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from pypost.ui.widgets.code_editor import CodeEditor
from pypost.ui.widgets.fold import BodyFormat
from pypost.ui.widgets.validate.json_body_validator import JsonBodyValidator


def _wait_for_validate(editor: CodeEditor) -> None:
    editor.validation_controller()._run_validate()


class TestJsonBodyValidator(unittest.TestCase):
    def test_valid_json_returns_no_errors(self):
        doc = QTextDocument()
        doc.setPlainText(json.dumps({"a": 1}, indent=2))
        errors = JsonBodyValidator().validate(doc)
        self.assertEqual(errors, [])

    def test_empty_body_returns_no_errors(self):
        doc = QTextDocument()
        doc.setPlainText("   \n  ")
        errors = JsonBodyValidator().validate(doc)
        self.assertEqual(errors, [])

    def test_invalid_json_reports_line_and_column(self):
        doc = QTextDocument()
        doc.setPlainText('{\n  "key": invalid\n}')
        errors = JsonBodyValidator().validate(doc)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].line, 2)
        self.assertGreater(errors[0].column, 0)
        self.assertTrue(errors[0].message)


class TestCodeEditorValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_valid_json_clears_error_display(self):
        editor = CodeEditor()
        editor.setPlainText('{"ok": true}')
        _wait_for_validate(editor)
        self.assertEqual(editor.validation_controller().errors(), [])
        self.assertEqual(editor.extraSelections(), [])

    def test_invalid_json_shows_error_banner(self):
        editor = CodeEditor()
        editor.show()
        editor.resize(400, 200)
        QTest.qWaitForWindowExposed(editor)
        editor.setPlainText("{bad")
        _wait_for_validate(editor)

        errors = editor.validation_controller().errors()
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].line, 1)

        label = editor.validation_controller()._error_label
        self.assertTrue(label.isVisible())
        self.assertIn("Line 1", label.text())

    def test_invalid_json_applies_extra_selections(self):
        editor = CodeEditor()
        editor.setPlainText('{\n  "x": bad\n}')
        _wait_for_validate(editor)
        self.assertGreater(len(editor.extraSelections()), 0)

    def test_plain_format_skips_validation(self):
        editor = CodeEditor()
        editor.set_body_format(BodyFormat.PLAIN)
        editor.setPlainText("{not json at all")
        _wait_for_validate(editor)
        self.assertEqual(editor.validation_controller().errors(), [])

    def test_set_plain_text_clears_errors(self):
        editor = CodeEditor()
        editor.setPlainText("{bad")
        _wait_for_validate(editor)
        self.assertEqual(len(editor.validation_controller().errors()), 1)

        editor.setPlainText('{"fixed": true}')
        self.assertEqual(editor.validation_controller().errors(), [])


if __name__ == "__main__":
    unittest.main()
