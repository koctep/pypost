"""CodeEditor format validation tests (PYPOST-512)."""

import pytest

pytestmark = pytest.mark.timeout(60)

import json
import unittest

from PySide6.QtGui import QTextDocument
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from pypost.ui.widgets.code_editor import CodeEditor
from pypost.ui.widgets.fold import BodyFormat
from pypost.ui.widgets.validate.json_body_validator import JsonBodyValidator
from pypost.ui.widgets.validate.xml_body_validator import XmlBodyValidator
from pypost.ui.widgets.validate.yaml_body_validator import YamlBodyValidator


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


class TestYamlBodyValidator(unittest.TestCase):
    def test_valid_yaml_returns_no_errors(self):
        doc = QTextDocument()
        doc.setPlainText("users:\n  - id: 1\n")
        errors = YamlBodyValidator().validate(doc)
        self.assertEqual(errors, [])

    def test_invalid_yaml_reports_line_and_column(self):
        doc = QTextDocument()
        doc.setPlainText("users:\n  - [")
        errors = YamlBodyValidator().validate(doc)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].line, 2)
        self.assertGreater(errors[0].column, 0)
        self.assertTrue(errors[0].message)


class TestXmlBodyValidator(unittest.TestCase):
    def test_valid_xml_returns_no_errors(self):
        doc = QTextDocument()
        doc.setPlainText("<root><item/></root>")
        errors = XmlBodyValidator().validate(doc)
        self.assertEqual(errors, [])

    def test_invalid_xml_reports_line_and_column(self):
        doc = QTextDocument()
        doc.setPlainText("<root><item></other></root>")
        errors = XmlBodyValidator().validate(doc)
        self.assertEqual(len(errors), 1)
        self.assertGreater(errors[0].line, 0)
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

    def test_invalid_yaml_shows_error_banner(self):
        editor = CodeEditor()
        editor.set_body_format(BodyFormat.YAML)
        editor.setPlainText("key:\n  - [")
        _wait_for_validate(editor)
        errors = editor.validation_controller().errors()
        self.assertEqual(len(errors), 1)
        self.assertIn("Line 2", editor.validation_controller()._error_label.text())

    def test_validation_error_line_correct_with_folded_blocks(self):
        editor = CodeEditor()
        valid = json.dumps({"a": {"b": 1}, "c": 2}, indent=2)
        editor.setPlainText(valid)
        editor.fold_controller()._run_scan()
        inner = next(
            r for r in editor.fold_controller().regions() if r.region_id == "/a"
        )
        editor.fold_controller().toggle(inner.region_id)

        broken = valid.replace('"c": 2', '"c": bad')
        cursor = editor.textCursor()
        cursor.select(cursor.SelectionType.Document)
        cursor.insertText(broken)
        _wait_for_validate(editor)

        errors = editor.validation_controller().errors()
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].line, 5)
        block = editor.document().findBlockByNumber(errors[0].line - 1)
        self.assertTrue(block.isValid())
        self.assertTrue(block.isVisible())
        self.assertIn("Line 5", editor.validation_controller()._error_label.text())

    def test_invalid_xml_shows_error_banner(self):
        editor = CodeEditor()
        editor.show()
        editor.resize(400, 200)
        QTest.qWaitForWindowExposed(editor)
        editor.set_body_format(BodyFormat.XML)
        editor.setPlainText("<root><item></other></root>")
        _wait_for_validate(editor)
        errors = editor.validation_controller().errors()
        self.assertEqual(len(errors), 1)
        self.assertIn("Line 1", editor.validation_controller()._error_label.text())


if __name__ == "__main__":
    unittest.main()
