"""JsonHighlighter tests (PYPOST-103).

PYPOST-100 (gap analysis): RequestEditor/ResponseView attach JsonHighlighter to JSON body
documents; rules cover keywords, numbers, strings, and object keys. Assertions use
QTextLayout format ranges (QTextCursor.charFormat ignores QSyntaxHighlighter ranges).
"""

import unittest

from PySide6.QtGui import QColor, QTextDocument
from PySide6.QtWidgets import QApplication, QTextEdit

from pypost.ui.widgets.json_highlighter import JsonHighlighter


def _hex_color_at(doc: QTextDocument, position: int) -> str:
    """Hex foreground from QSyntaxHighlighter ranges at document position."""
    block = doc.findBlock(position)
    if not block.isValid():
        return "#000000"
    rel = position - block.position()
    layout = block.layout()
    if layout is None:
        return "#000000"
    for r in layout.formats():
        if r.start <= rel < r.start + r.length:
            c = r.format.foreground().color()
            return c.name(QColor.NameFormat.HexRgb)
    return "#000000"


class TestJsonHighlighter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _edit_with_highlighted(self, text: str) -> QTextEdit:
        edit = QTextEdit()
        highlighter = JsonHighlighter(edit.document())
        edit.setPlainText(text)
        highlighter.rehighlight()
        edit._highlighter = highlighter
        return edit

    def test_highlights_json_true_keyword(self):
        text = '{"enabled": true}'
        edit = self._edit_with_highlighted(text)
        pos = text.index("true")
        self.assertEqual(_hex_color_at(edit.document(), pos), QColor("darkblue").name())

    def test_highlights_json_false_and_null(self):
        text = '{"a": false, "b": null}'
        edit = self._edit_with_highlighted(text)
        darkblue = QColor("darkblue").name()
        p_false = text.index("false")
        p_null = text.index("null")
        self.assertEqual(_hex_color_at(edit.document(), p_false), darkblue)
        self.assertEqual(_hex_color_at(edit.document(), p_null), darkblue)

    def test_highlights_json_number(self):
        text = '{"n": -3.14}'
        edit = self._edit_with_highlighted(text)
        # Number rule does not include leading '-'; digit run is blue.
        pos = text.index("3")
        self.assertEqual(_hex_color_at(edit.document(), pos), QColor("blue").name())

    def test_highlights_json_string_value_green(self):
        text = '{"k": "hello"}'
        edit = self._edit_with_highlighted(text)
        pos = text.index("h")
        self.assertEqual(_hex_color_at(edit.document(), pos), QColor("green").name())

    def test_highlights_json_object_key_purple(self):
        text = '{"mykey": 1}'
        edit = self._edit_with_highlighted(text)
        pos = text.index("m")
        self.assertEqual(_hex_color_at(edit.document(), pos), QColor("purple").name())

    def test_multiline_json_still_highlights(self):
        text = '{\n  "x": true\n}'
        edit = self._edit_with_highlighted(text)
        pos = text.index("true")
        self.assertEqual(_hex_color_at(edit.document(), pos), QColor("darkblue").name())

    def test_empty_document_does_not_raise(self):
        edit = QTextEdit()
        hl = JsonHighlighter(edit.document())
        edit.setPlainText("")
        hl.rehighlight()
        self.assertEqual(edit.toPlainText(), "")


if __name__ == "__main__":
    unittest.main()
