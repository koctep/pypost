"""CodeEditor unit tests (PYPOST-108, PYPOST-110, PYPOST-510).

PYPOST-104: CodeEditor extends VariableAwarePlainTextEdit; used in RequestEditor for JSON body.
Coverage: indent/tab stops, JSON reformat, paste-as-JSON-format, Enter auto-indent, closing-bracket
dedent when line is whitespace-only.
PYPOST-510: line-number gutter width, viewport margin, read-only gutter clicks.
"""

import json
import unittest
from unittest.mock import patch

from PySide6.QtCore import QEvent, Qt, QMimeData, QPoint, QRect
from PySide6.QtGui import QKeyEvent, QPaintEvent, QPainter, QTextCursor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPlainTextEdit

from pypost.core.yaml_json_converter import convert_yaml_body_to_object
from pypost.ui.widgets.code_editor import CodeEditor
from pypost.ui.widgets.fold import BodyFormat


def _collect_gutter_numbers(editor: CodeEditor) -> list[str]:
    editor.show()
    editor.resize(400, 300)
    QTest.qWaitForWindowExposed(editor)
    width = editor.line_number_area_width()
    editor._line_number_area.setGeometry(0, 0, width, editor.height())
    drawn: list[str] = []
    original = QPainter.drawText

    def capture(painter, *args, **kwargs):
        if args and isinstance(args[-1], str):
            drawn.append(args[-1])
        return original(painter, *args, **kwargs)

    with patch.object(QPainter, "drawText", capture):
        rect = QRect(0, 0, width, editor.height())
        editor.line_number_area_paint_event(QPaintEvent(rect))

    return drawn


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

    def test_insert_from_mime_data_json_to_yaml_when_yaml_as_json(self):
        ed = CodeEditor()
        ed.set_body_format(BodyFormat.YAML)
        ed.set_yaml_as_json(True)
        ed.setPlainText("")
        mime = QMimeData()
        mime.setText('{"x": 1, "items": ["a", "b"]}')
        ed.insertFromMimeData(mime)
        self.assertEqual(
            convert_yaml_body_to_object(ed.toPlainText()),
            {"x": 1, "items": ["a", "b"]},
        )

    def test_insert_from_mime_data_json_stays_json_without_yaml_as_json(self):
        ed = CodeEditor(indent_size=2)
        ed.set_body_format(BodyFormat.YAML)
        ed.set_yaml_as_json(False)
        ed.setPlainText("")
        mime = QMimeData()
        mime.setText('{"x": 1}')
        ed.insertFromMimeData(mime)
        self.assertEqual(json.loads(ed.toPlainText()), {"x": 1})

    def test_insert_from_mime_data_json_stays_json_for_json_format(self):
        ed = CodeEditor(indent_size=2)
        ed.set_body_format(BodyFormat.JSON)
        ed.set_yaml_as_json(True)
        ed.setPlainText("")
        mime = QMimeData()
        mime.setText('{"x": 1}')
        ed.insertFromMimeData(mime)
        self.assertEqual(json.loads(ed.toPlainText()), {"x": 1})


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


class TestCodeEditorLineNumbers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_empty_document_has_single_digit_gutter_width(self):
        ed = CodeEditor()
        self.assertEqual(ed.blockCount(), 1)
        self.assertGreater(ed.line_number_area_width(), 0)

    def test_viewport_margin_matches_gutter_width(self):
        ed = CodeEditor()
        ed.setPlainText("line one\nline two")
        margin = ed.viewportMargins().left()
        self.assertEqual(margin, ed.line_number_area_width())

    def test_gutter_width_grows_at_ten_lines(self):
        ed = CodeEditor()
        ed.setPlainText("\n".join(str(i) for i in range(1, 10)))
        width_nine = ed.line_number_area_width()
        ed.setPlainText("\n".join(str(i) for i in range(1, 11)))
        self.assertGreater(ed.line_number_area_width(), width_nine)

    def test_gutter_width_grows_at_hundred_lines(self):
        ed = CodeEditor()
        ed.setPlainText("\n".join(str(i) for i in range(1, 100)))
        width_99 = ed.line_number_area_width()
        ed.setPlainText("\n".join(str(i) for i in range(1, 101)))
        self.assertGreater(ed.line_number_area_width(), width_99)

    def test_gutter_width_shrinks_when_lines_removed(self):
        ed = CodeEditor()
        ed.setPlainText("\n".join(str(i) for i in range(1, 11)))
        width_ten = ed.line_number_area_width()
        ed.setPlainText("\n".join(str(i) for i in range(1, 10)))
        self.assertLess(ed.line_number_area_width(), width_ten)

    def test_gutter_click_does_not_modify_document(self):
        ed = CodeEditor()
        ed.setPlainText('{"a": 1}')
        ed.show()
        QTest.qWaitForWindowExposed(ed)
        before = ed.toPlainText()
        gutter_x = ed.viewportMargins().left() // 2
        QTest.mouseClick(ed._line_number_area, Qt.MouseButton.LeftButton, pos=QPoint(gutter_x, 5))
        self.assertEqual(ed.toPlainText(), before)

    def test_empty_document_paints_line_number_one(self):
        ed = CodeEditor()
        self.assertEqual(ed.blockCount(), 1)
        numbers = _collect_gutter_numbers(ed)
        self.assertEqual(numbers, ["1"])

    def test_two_lines_paint_correct_numbers(self):
        ed = CodeEditor()
        ed.setPlainText("first\nsecond")
        numbers = _collect_gutter_numbers(ed)
        self.assertEqual(numbers, ["1", "2"])

    def test_typing_newline_updates_line_numbers(self):
        ed = CodeEditor()
        ed.setPlainText("one")
        ed.show()
        QTest.qWaitForWindowExposed(ed)
        cur = ed.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.End)
        ed.setTextCursor(cur)
        QTest.keyClick(ed, Qt.Key.Key_Return)
        self.assertEqual(ed.blockCount(), 2)
        numbers = _collect_gutter_numbers(ed)
        self.assertEqual(numbers[:2], ["1", "2"])

    def test_paste_adds_lines_updates_line_numbers(self):
        ed = CodeEditor()
        ed.setPlainText("")
        mime = QMimeData()
        mime.setText("alpha\nbeta\ngamma")
        ed.insertFromMimeData(mime)
        self.assertEqual(ed.blockCount(), 3)
        numbers = _collect_gutter_numbers(ed)
        self.assertEqual(numbers, ["1", "2", "3"])

    def test_delete_line_updates_line_numbers(self):
        ed = CodeEditor()
        ed.setPlainText("keep\nremove")
        ed.show()
        QTest.qWaitForWindowExposed(ed)
        cur = ed.textCursor()
        cur.movePosition(QTextCursor.MoveOperation.End)
        cur.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cur.movePosition(
            QTextCursor.MoveOperation.Up,
            QTextCursor.MoveMode.KeepAnchor,
        )
        cur.removeSelectedText()
        self.assertEqual(ed.blockCount(), 1)
        numbers = _collect_gutter_numbers(ed)
        self.assertEqual(numbers, ["1"])

    def test_gutter_key_event_does_not_modify_document(self):
        ed = CodeEditor()
        ed.setPlainText('{"a": 1}')
        before = ed.toPlainText()
        event = QKeyEvent(
            QEvent.Type.KeyPress,
            Qt.Key.Key_A,
            Qt.KeyboardModifier.NoModifier,
            "a",
        )
        QApplication.sendEvent(ed._line_number_area, event)
        self.assertEqual(ed.toPlainText(), before)

    def test_resize_updates_gutter_geometry(self):
        ed = CodeEditor()
        ed.setPlainText("a\nb\nc")
        ed.show()
        QTest.qWaitForWindowExposed(ed)
        ed.resize(500, 400)
        QApplication.processEvents()
        cr = ed.contentsRect()
        gutter = ed._line_number_area
        self.assertEqual(gutter.width(), ed.line_number_area_width())
        self.assertEqual(gutter.height(), cr.height())

    def test_scroll_keeps_gutter_full_height(self):
        ed = CodeEditor()
        ed.setPlainText("\n".join(f"line {i}" for i in range(1, 51)))
        ed.show()
        ed.resize(200, 120)
        QTest.qWaitForWindowExposed(ed)
        ed.verticalScrollBar().setValue(ed.verticalScrollBar().maximum())
        QApplication.processEvents()
        self.assertEqual(ed._line_number_area.height(), ed.contentsRect().height())


if __name__ == "__main__":
    unittest.main()
