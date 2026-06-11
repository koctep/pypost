"""JsonHighlighter tests (PYPOST-103, PYPOST-124, PYPOST-399, PYPOST-398, PYPOST-395).

RequestEditor/ResponseView attach JsonHighlighter to JSON body documents. Rules cover
keywords, numbers, strings, object keys, and template placeholders. Assertions use
QTextLayout format ranges (QTextCursor.charFormat ignores QSyntaxHighlighter ranges).
"""

import pytest

pytestmark = pytest.mark.timeout(60)

import unittest

from PySide6.QtGui import QColor, QTextDocument
from PySide6.QtWidgets import QApplication, QTextEdit

from pypost.ui.theme.json_syntax_theme import (
    DARK_JSON_SYNTAX_COLORS,
    DEFAULT_JSON_SYNTAX_COLORS,
    JsonSyntaxColors,
    resolve_json_syntax_colors,
)
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

    def test_highlights_integer_number(self):
        text = '{"count": 42}'
        edit = self._edit_with_highlighted(text)
        pos = text.index("42")
        self.assertEqual(_hex_color_at(edit.document(), pos), QColor("blue").name())

    def test_highlights_zero_number(self):
        text = '{"n": 0}'
        edit = self._edit_with_highlighted(text)
        pos = text.index("0", text.index(":"))
        self.assertEqual(_hex_color_at(edit.document(), pos), QColor("blue").name())

    def test_highlights_scientific_notation_number(self):
        text = '{"x": 1.5e10}'
        edit = self._edit_with_highlighted(text)
        pos = text.index("1")
        self.assertEqual(_hex_color_at(edit.document(), pos), QColor("blue").name())
        pos_exp = text.index("e")
        self.assertEqual(_hex_color_at(edit.document(), pos_exp), QColor("blue").name())

    def test_highlights_json_string_value_green(self):
        text = '{"k": "hello"}'
        edit = self._edit_with_highlighted(text)
        pos = text.index("h")
        self.assertEqual(_hex_color_at(edit.document(), pos), QColor("green").name())

    def test_highlights_array_string_green_not_purple(self):
        text = '["item"]'
        edit = self._edit_with_highlighted(text)
        pos = text.index("i")
        self.assertEqual(_hex_color_at(edit.document(), pos), QColor("green").name())

    def test_highlights_escaped_characters_in_string(self):
        text = '{"m": "a\\"b"}'
        edit = self._edit_with_highlighted(text)
        pos = text.index("a", text.index(":"))
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

    def test_combined_json_syntax_colors(self):
        text = '{"enabled": true, "name": "api", "count": 7}'
        edit = self._edit_with_highlighted(text)
        darkblue = QColor("darkblue").name()
        purple = QColor("purple").name()
        green = QColor("green").name()
        blue = QColor("blue").name()
        self.assertEqual(_hex_color_at(edit.document(), text.index("enabled")), purple)
        self.assertEqual(_hex_color_at(edit.document(), text.index("true")), darkblue)
        self.assertEqual(_hex_color_at(edit.document(), text.index("name")), purple)
        self.assertEqual(_hex_color_at(edit.document(), text.index("api")), green)
        self.assertEqual(_hex_color_at(edit.document(), text.index("count")), purple)
        self.assertEqual(_hex_color_at(edit.document(), text.index("7")), blue)

    def test_highlights_template_variable_in_string_value(self):
        text = '{"url": "{{baseUrl}}/api"}'
        edit = self._edit_with_highlighted(text)
        pos = text.index("baseUrl")
        self.assertEqual(_hex_color_at(edit.document(), pos), QColor("darkorange").name())

    def test_highlights_function_expression_placeholder(self):
        text = '{"path": "{{urlencode(db)}}"}'
        edit = self._edit_with_highlighted(text)
        pos = text.index("urlencode")
        self.assertEqual(_hex_color_at(edit.document(), pos), QColor("darkorange").name())

    def test_variable_highlight_overrides_string_green(self):
        text = '{"k": "{{x}}"}'
        edit = self._edit_with_highlighted(text)
        brace_pos = text.index("{{")
        self.assertEqual(_hex_color_at(edit.document(), brace_pos), QColor("darkorange").name())

    def test_empty_document_does_not_raise(self):
        edit = QTextEdit()
        hl = JsonHighlighter(edit.document())
        edit.setPlainText("")
        hl.rehighlight()
        self.assertEqual(edit.toPlainText(), "")

    def test_custom_theme_colors_are_applied(self):
        colors = JsonSyntaxColors(
            keyword="red",
            number="cyan",
            string="magenta",
            key="yellow",
            placeholder="gray",
        )
        text = '{"k": true, "n": 1, "s": "{{x}}"}'
        edit = QTextEdit()
        highlighter = JsonHighlighter(edit.document(), colors=colors)
        edit.setPlainText(text)
        highlighter.rehighlight()
        self.assertEqual(_hex_color_at(edit.document(), text.index("k")), QColor("yellow").name())
        self.assertEqual(_hex_color_at(edit.document(), text.index("true")), QColor("red").name())
        self.assertEqual(_hex_color_at(edit.document(), text.index("1")), QColor("cyan").name())
        self.assertEqual(_hex_color_at(edit.document(), text.index("{{")), QColor("gray").name())

    def test_dark_palette_colors_are_applied(self):
        text = '{"enabled": true, "name": "api", "count": 7, "url": "{{host}}"}'
        edit = QTextEdit()
        highlighter = JsonHighlighter(edit.document(), colors=DARK_JSON_SYNTAX_COLORS)
        edit.setPlainText(text)
        highlighter.rehighlight()
        dark = DARK_JSON_SYNTAX_COLORS
        self.assertEqual(
            _hex_color_at(edit.document(), text.index("enabled")),
            QColor(dark.key).name(),
        )
        self.assertEqual(
            _hex_color_at(edit.document(), text.index("true")),
            QColor(dark.keyword).name(),
        )
        self.assertEqual(
            _hex_color_at(edit.document(), text.index("api")),
            QColor(dark.string).name(),
        )
        self.assertEqual(
            _hex_color_at(edit.document(), text.index("7")),
            QColor(dark.number).name(),
        )
        self.assertEqual(
            _hex_color_at(edit.document(), text.index("host")),
            QColor(dark.placeholder).name(),
        )

    def test_resolve_json_syntax_colors_returns_light_by_default(self):
        self.assertEqual(resolve_json_syntax_colors(dark=False), DEFAULT_JSON_SYNTAX_COLORS)
        self.assertEqual(resolve_json_syntax_colors(dark=True), DARK_JSON_SYNTAX_COLORS)

    def test_set_colors_rebinds_highlighting(self):
        text = '{"k": true}'
        edit = QTextEdit()
        highlighter = JsonHighlighter(edit.document(), colors=DEFAULT_JSON_SYNTAX_COLORS)
        edit.setPlainText(text)
        highlighter.rehighlight()
        self.assertEqual(
            _hex_color_at(edit.document(), text.index("true")),
            QColor("darkblue").name(),
        )
        highlighter.set_colors(DARK_JSON_SYNTAX_COLORS)
        self.assertEqual(
            _hex_color_at(edit.document(), text.index("true")),
            QColor(DARK_JSON_SYNTAX_COLORS.keyword).name(),
        )


if __name__ == "__main__":
    unittest.main()
