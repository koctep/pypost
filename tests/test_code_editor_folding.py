"""CodeEditor folding tests (PYPOST-511)."""

import json
import unittest

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QPaintEvent, QPainter, QTextCursor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from pypost.ui.widgets.code_editor import CodeEditor
from pypost.ui.widgets.fold.json_structure_scanner import JsonStructureScanner


def _wait_for_scan(editor: CodeEditor) -> None:
    editor.fold_controller()._run_scan()


def _root_region(editor: CodeEditor):
    regions = editor.fold_controller().regions()
    return next(r for r in regions if r.region_id == "/")


def _visible_block_numbers(editor: CodeEditor) -> list[int]:
    block = editor.document().firstBlock()
    numbers: list[int] = []
    while block.isValid():
        if block.isVisible():
            numbers.append(block.blockNumber())
        block = block.next()
    return numbers


def _collect_gutter_numbers(editor: CodeEditor) -> list[str]:
    editor.show()
    editor.resize(400, 300)
    QTest.qWaitForWindowExposed(editor)
    width = editor.line_number_area_width()
    editor._line_number_area.setGeometry(0, 0, width, editor.height())
    drawn: list[str] = []
    original = QPainter.drawText

    def capture(painter, *args, **kwargs):
        if args and isinstance(args[-1], str) and args[-1].isdigit():
            drawn.append(args[-1])
        return original(painter, *args, **kwargs)

    from unittest.mock import patch

    with patch.object(QPainter, "drawText", capture):
        rect = QRect(0, 0, width, editor.height())
        editor.line_number_area_paint_event(QPaintEvent(rect))

    return drawn


_NESTED_JSON = json.dumps(
    {"users": [{"id": 1, "name": "Ada"}, {"id": 2, "name": "Bob"}]},
    indent=2,
)

_REMAP_JSON = json.dumps({"a": {"b": 1}, "c": 2}, indent=2)


class TestJsonStructureScanner(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_valid_nested_json_finds_regions(self):
        from PySide6.QtGui import QTextDocument

        doc = QTextDocument()
        doc.setPlainText(_NESTED_JSON)
        regions = JsonStructureScanner().scan(doc)
        self.assertGreater(len(regions), 0)

    def test_invalid_json_returns_no_regions(self):
        from PySide6.QtGui import QTextDocument

        doc = QTextDocument()
        doc.setPlainText("{not valid")
        regions = JsonStructureScanner().scan(doc)
        self.assertEqual(regions, [])


class TestCodeEditorFolding(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_collapse_hides_descendant_blocks(self):
        ed = CodeEditor()
        ed.setPlainText(_NESTED_JSON)
        _wait_for_scan(ed)
        regions = ed.fold_controller().regions()
        self.assertGreater(len(regions), 0)

        root = _root_region(ed)
        ed.fold_controller().toggle(root.region_id)
        visible = _visible_block_numbers(ed)
        for block_num in range(root.start_block + 1, root.end_block + 1):
            self.assertNotIn(block_num, visible)
        self.assertIn(root.header_block, visible)

    def test_collapse_preserves_plain_text(self):
        ed = CodeEditor()
        ed.setPlainText(_NESTED_JSON)
        _wait_for_scan(ed)
        before = ed.toPlainText()
        root = _root_region(ed)
        ed.fold_controller().toggle(root.region_id)
        self.assertEqual(ed.toPlainText(), before)

    def test_expand_restores_visibility(self):
        ed = CodeEditor()
        ed.setPlainText(_NESTED_JSON)
        _wait_for_scan(ed)
        root = _root_region(ed)
        ed.fold_controller().toggle(root.region_id)
        ed.fold_controller().toggle(root.region_id)
        self.assertEqual(
            _visible_block_numbers(ed),
            list(range(ed.blockCount())),
        )

    def test_nested_collapse_multiple_levels(self):
        ed = CodeEditor()
        ed.setPlainText(_NESTED_JSON)
        _wait_for_scan(ed)
        regions = ed.fold_controller().regions()
        self.assertGreaterEqual(len(regions), 2)

        root = _root_region(ed)
        users = next(r for r in regions if r.region_id == "/users")
        ed.fold_controller().toggle(root.region_id)
        ed.fold_controller().toggle(users.region_id)
        visible = _visible_block_numbers(ed)
        for region in (root, users):
            for block_num in range(region.start_block + 1, region.end_block + 1):
                self.assertNotIn(block_num, visible)

    def test_invalid_json_no_fold_regions(self):
        ed = CodeEditor()
        ed.setPlainText("{broken")
        _wait_for_scan(ed)
        self.assertEqual(ed.fold_controller().regions(), [])
        self.assertEqual(_visible_block_numbers(ed), list(range(ed.blockCount())))

    def test_logical_line_numbers_with_collapsed_lines(self):
        ed = CodeEditor()
        ed.setPlainText(_NESTED_JSON)
        _wait_for_scan(ed)
        root = _root_region(ed)
        ed.fold_controller().toggle(root.region_id)
        numbers = _collect_gutter_numbers(ed)
        self.assertTrue(all(int(n) > 0 for n in numbers))
        if len(numbers) >= 2:
            self.assertGreater(int(numbers[1]), int(numbers[0]))

    def test_gutter_chevron_click_toggles_fold(self):
        ed = CodeEditor()
        ed.setPlainText(_NESTED_JSON)
        _wait_for_scan(ed)
        ed.show()
        QTest.qWaitForWindowExposed(ed)
        root = _root_region(ed)
        self.assertFalse(ed.fold_controller().is_collapsed(root.region_id))

        ed.show()
        QTest.qWaitForWindowExposed(ed)
        block = ed.document().findBlockByNumber(root.header_block)
        top = round(
            ed.blockBoundingGeometry(block).translated(ed.contentOffset()).top()
        )
        gutter_y = top + ed.fontMetrics().height() // 2
        QTest.mouseClick(
            ed._line_number_area,
            Qt.MouseButton.LeftButton,
            pos=QPoint(3, gutter_y),
        )
        self.assertTrue(ed.fold_controller().is_collapsed(root.region_id))
        self.assertEqual(ed.toPlainText(), _NESTED_JSON)

    def test_set_plain_text_expands_all(self):
        ed = CodeEditor()
        ed.setPlainText(_NESTED_JSON)
        _wait_for_scan(ed)
        root = _root_region(ed)
        ed.fold_controller().toggle(root.region_id)
        ed.setPlainText(_NESTED_JSON)
        _wait_for_scan(ed)
        self.assertEqual(
            _visible_block_numbers(ed),
            list(range(ed.blockCount())),
        )


def _replace_once(editor: CodeEditor, old: str, new: str) -> None:
    cursor = editor.textCursor()
    cursor.beginEditBlock()
    full = editor.toPlainText()
    start = full.index(old)
    cursor.setPosition(start)
    cursor.setPosition(start + len(old), QTextCursor.MoveMode.KeepAnchor)
    cursor.insertText(new)
    cursor.endEditBlock()


class TestFoldRemappingAfterEdits(unittest.TestCase):
    """PYPOST-517: collapse state survives edits when region boundaries are unchanged."""

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_collapse_preserved_when_edit_outside_region(self):
        ed = CodeEditor()
        ed.setPlainText(_REMAP_JSON)
        _wait_for_scan(ed)
        inner = next(r for r in ed.fold_controller().regions() if r.region_id == "/a")
        ed.fold_controller().toggle(inner.region_id)
        self.assertTrue(ed.fold_controller().is_collapsed(inner.region_id))

        _replace_once(ed, '"c": 2', '"c": 3')
        _wait_for_scan(ed)
        self.assertTrue(ed.fold_controller().is_collapsed(inner.region_id))
        visible = _visible_block_numbers(ed)
        for block_num in range(inner.start_block + 1, inner.end_block + 1):
            self.assertNotIn(block_num, visible)

    def test_collapse_dropped_when_region_boundaries_change(self):
        ed = CodeEditor()
        ed.setPlainText(_REMAP_JSON)
        _wait_for_scan(ed)
        inner = next(r for r in ed.fold_controller().regions() if r.region_id == "/a")
        ed.fold_controller().toggle(inner.region_id)
        self.assertTrue(ed.fold_controller().is_collapsed(inner.region_id))

        _replace_once(ed, '"b": 1', '"b": 1,\n    "x": 0')
        _wait_for_scan(ed)
        self.assertFalse(ed.fold_controller().is_collapsed(inner.region_id))
        self.assertEqual(
            _visible_block_numbers(ed),
            list(range(ed.blockCount())),
        )

    def test_nested_collapse_remapping_after_paste_outside(self):
        ed = CodeEditor()
        ed.setPlainText(_NESTED_JSON)
        _wait_for_scan(ed)
        users = next(r for r in ed.fold_controller().regions() if r.region_id == "/users")
        ed.fold_controller().toggle(users.region_id)
        self.assertTrue(ed.fold_controller().is_collapsed(users.region_id))

        _replace_once(ed, "  ]\n}", '  ],\n  "tag": "v1"\n}')
        _wait_for_scan(ed)
        self.assertTrue(ed.fold_controller().is_collapsed(users.region_id))
        visible = _visible_block_numbers(ed)
        for block_num in range(users.start_block + 1, users.end_block + 1):
            self.assertNotIn(block_num, visible)

    def test_nested_collapse_dropped_after_bracket_edit_inside_region(self):
        ed = CodeEditor()
        ed.setPlainText(_NESTED_JSON)
        _wait_for_scan(ed)
        users = next(r for r in ed.fold_controller().regions() if r.region_id == "/users")
        first_user = next(
            r for r in ed.fold_controller().regions() if r.region_id == "/users/0"
        )
        ed.fold_controller().toggle(users.region_id)
        ed.fold_controller().toggle(first_user.region_id)
        self.assertTrue(ed.fold_controller().is_collapsed(users.region_id))
        self.assertTrue(ed.fold_controller().is_collapsed(first_user.region_id))

        _replace_once(ed, '"name": "Ada"', '"name": "Ada",\n      "role": "admin"')
        _wait_for_scan(ed)
        self.assertFalse(ed.fold_controller().is_collapsed(first_user.region_id))
        self.assertFalse(ed.fold_controller().is_collapsed(users.region_id))


if __name__ == "__main__":
    unittest.main()
