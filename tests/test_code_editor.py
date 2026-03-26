"""CodeEditor unit tests (PYPOST-108, PYPOST-110).

PYPOST-104: CodeEditor extends VariableAwarePlainTextEdit; used in RequestEditor for JSON body.
Coverage: indent/tab stops, JSON reformat, paste-as-JSON-format, Enter auto-indent, closing-bracket
dedent when line is whitespace-only.
"""

import json
import unittest

from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QTextCursor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPlainTextEdit

from pypost.ui.widgets.code_editor import CodeEditor


class TestCodeEditorBasics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_line_wrap_disabled(self):
        ed = CodeEditor()
        self.assertEqual(ed.lineWrapMode(), QPlainTextEdit.LineWrapMode.NoWrap)

    def test_default_indent_size(self):
        ed = CodeEditor()
        self.assertEqual(ed.indent_size, 2)

    def test_update_indent_size_updates_tab_stop_distance(self):
        ed = CodeEditor(indent_size=2)
        d2 = ed.tabStopDistance()
        ed.update_indent_size(4)
        self.assertEqual(ed.indent_size, 4)
        self.assertGreater(ed.tabStopDistance(), d2)


class TestCodeEditorReformat(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_reformat_text_valid_json(self):
        ed = CodeEditor(indent_size=2)
        raw = '{"a":1,"b":[2]}'
        ed.setPlainText(raw)
        ed.reformat_text()
        parsed = json.loads(ed.toPlainText())
        self.assertEqual(parsed, {"a": 1, "b": [2]})
        self.assertIn("\n", ed.toPlainText())

    def test_reformat_text_respects_indent_size_four(self):
        ed = CodeEditor(indent_size=4)
        ed.setPlainText('{"a": 1}')
        ed.reformat_text()
        self.assertIn("    ", ed.toPlainText())
        self.assertEqual(json.loads(ed.toPlainText()), {"a": 1})

    def test_reformat_text_invalid_json_unchanged(self):
        ed = CodeEditor()
        bad = "{not json"
        ed.setPlainText(bad)
        ed.reformat_text()
        self.assertEqual(ed.toPlainText(), bad)

    def test_reformat_text_empty_noop(self):
        ed = CodeEditor()
        ed.reformat_text()
        self.assertEqual(ed.toPlainText(), "")


class TestCodeEditorPaste(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_insert_from_mime_data_formats_json(self):
        ed = CodeEditor(indent_size=2)
        ed.setPlainText("")
        mime = QMimeData()
        mime.setText('{"x": 1}')
        ed.insertFromMimeData(mime)
        self.assertEqual(json.loads(ed.toPlainText()), {"x": 1})

    def test_insert_from_mime_data_non_json_passthrough(self):
        ed = CodeEditor()
        ed.setPlainText("keep")
        cur = ed.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.End)
        ed.setTextCursor(cur)
        mime = QMimeData()
        mime.setText("hello {{var}}")
        ed.insertFromMimeData(mime)
        self.assertEqual(ed.toPlainText(), "keephello {{var}}")


class TestCodeEditorKeyHandling(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_enter_after_open_brace_adds_indented_newline(self):
        ed = CodeEditor(indent_size=2)
        ed.setPlainText("{")
        cur = ed.textCursor()
        cur.movePosition(cur.MoveOperation.End)
        ed.setTextCursor(cur)
        QTest.keyClick(ed, Qt.Key.Key_Return)
        self.assertEqual(ed.toPlainText(), "{\n  ")

    def test_enter_after_open_bracket_indents(self):
        ed = CodeEditor(indent_size=2)
        ed.setPlainText("[")
        cur = ed.textCursor()
        cur.movePosition(cur.MoveOperation.End)
        ed.setTextCursor(cur)
        QTest.keyClick(ed, Qt.Key.Key_Return)
        self.assertEqual(ed.toPlainText(), "[\n  ")

    def test_closing_bracket_dedents_whitespace_only_line(self):
        ed = CodeEditor(indent_size=2)
        ed.setPlainText("{\n  ")
        cur = ed.textCursor()
        cur.movePosition(cur.MoveOperation.End)
        ed.setTextCursor(cur)
        QTest.keyClick(ed, Qt.Key.Key_BraceRight)
        self.assertEqual(ed.toPlainText(), "{\n}")


if __name__ == "__main__":
    unittest.main()
