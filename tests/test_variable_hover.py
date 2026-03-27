"""Variable hover tests (PYPOST-117–121, PYPOST-130–133).

PYPOST-117 / PYPOST-121: VariableHoverHelper + VariableHoverMixin for URL/body fields
(VariableAwarePlainTextEdit / VariableAwareLineEdit).

PYPOST-118: QToolTip + LineEdit (fixed cursor) contract.

PYPOST-130 / PYPOST-133: resolve_text edge cases (batch 2 / PYPOST-15 path).

PYPOST-131: QToolTip + PlainTextEdit (JSON body) contract, same mixin as CodeEditor body.
"""

import unittest
from typing import Tuple
from unittest.mock import patch

from PySide6.QtCore import QEvent, QPoint, Qt
from PySide6.QtGui import QMouseEvent, QTextCursor
from PySide6.QtWidgets import QApplication, QLineEdit, QPlainTextEdit

from pypost.ui.widgets.mixins import (
    HIDDEN_MASK,
    VariableHoverHelper,
    VariableHoverMixin,
)


class _FixedCursorHoverLineEdit(VariableHoverMixin, QLineEdit):
    """Same MRO as VariableAwareLineEdit; Python cursorPositionAt for stable tests."""

    def __init__(self) -> None:
        QLineEdit.__init__(self)
        VariableHoverMixin.__init__(self)
        self.fixed_cursor_index = 0

    def cursorPositionAt(self, pos):  # noqa: ARG002
        return self.fixed_cursor_index

    def _get_text_at_cursor(self, event) -> Tuple[str, int]:
        text = self.text()
        if not text:
            return "", 0
        pos = event.position().toPoint()
        index = self.cursorPositionAt(pos)
        return text, index


class _FixedCursorHoverPlainText(VariableHoverMixin, QPlainTextEdit):
    """Same pattern as VariableAwarePlainTextEdit; stable cursorForPosition for tests."""

    def __init__(self) -> None:
        QPlainTextEdit.__init__(self)
        VariableHoverMixin.__init__(self)
        self.fixed_document_position = 0

    def cursorForPosition(self, pos):  # noqa: ARG002
        cur = QTextCursor(self.document())
        text = self.toPlainText()
        pos_idx = min(self.fixed_document_position, len(text))
        cur.setPosition(pos_idx)
        return cur

    def _get_text_at_cursor(self, event) -> Tuple[str, int]:
        text = self.toPlainText()
        if not text:
            return "", 0
        cursor = self.cursorForPosition(event.position().toPoint())
        return text, cursor.position()


class TestVariableHoverHelper(unittest.TestCase):
    def test_find_variable_at_index_inside_name(self):
        text = "x{{foo}}y"
        idx = text.index("f")
        self.assertEqual(VariableHoverHelper.find_variable_at_index(text, idx), "foo")

    def test_find_variable_at_index_on_open_brace(self):
        text = "{{bar}}"
        idx = text.index("{")
        self.assertEqual(VariableHoverHelper.find_variable_at_index(text, idx), "bar")

    def test_find_variable_at_index_outside_returns_none(self):
        self.assertIsNone(VariableHoverHelper.find_variable_at_index("plain", 2))

    def test_get_variable_value_defined(self):
        self.assertEqual(
            VariableHoverHelper.get_variable_value("a", {"a": "v"}),
            "v",
        )

    def test_get_variable_value_missing(self):
        self.assertEqual(
            VariableHoverHelper.get_variable_value("missing", {}),
            "<not defined>",
        )

    def test_get_variable_value_hidden_returns_mask(self):
        self.assertEqual(
            VariableHoverHelper.get_variable_value(
                "token",
                {"token": "abc"},
                {"token"},
            ),
            HIDDEN_MASK,
        )

    def test_resolve_text_replaces_all(self):
        out = VariableHoverHelper.resolve_text(
            "{{a}} and {{b}}",
            {"a": "1", "b": "2"},
        )
        self.assertEqual(out, "1 and 2")

    def test_resolve_text_undefined_placeholder(self):
        out = VariableHoverHelper.resolve_text("{{only}}", {})
        self.assertEqual(out, "<not defined>")

    def test_resolve_text_repeated_variable(self):
        out = VariableHoverHelper.resolve_text("{{x}}-{{x}}", {"x": "ok"})
        self.assertEqual(out, "ok-ok")

    def test_resolve_text_adjacent_placeholders(self):
        out = VariableHoverHelper.resolve_text("{{a}}{{b}}", {"a": "1", "b": "2"})
        self.assertEqual(out, "12")

    def test_resolve_text_empty_string(self):
        self.assertEqual(VariableHoverHelper.resolve_text("", {"a": "b"}), "")

    def test_resolve_text_no_placeholders_unchanged(self):
        self.assertEqual(
            VariableHoverHelper.resolve_text("plain", {}),
            "plain",
        )

    def test_resolve_text_underscore_name(self):
        out = VariableHoverHelper.resolve_text("{{my_var}}", {"my_var": "v"})
        self.assertEqual(out, "v")

    def test_resolve_text_hidden_placeholder_returns_mask(self):
        out = VariableHoverHelper.resolve_text(
            "token={{token}}",
            {"token": "abc"},
            {"token"},
        )
        self.assertEqual(out, f"token={HIDDEN_MASK}")


def _mouse_move_event(widget, local_point: QPoint) -> QMouseEvent:
    return QMouseEvent(
        QEvent.Type.MouseMove,
        local_point,
        widget.mapToGlobal(local_point),
        Qt.MouseButton.NoButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )


class TestVariableAwareLineEditTooltips(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    @patch("pypost.ui.widgets.mixins.QToolTip.hideText")
    @patch("pypost.ui.widgets.mixins.QToolTip.showText")
    def test_mouse_over_variable_shows_resolved_tooltip(self, show_mock, _hide):
        w = _FixedCursorHoverLineEdit()
        w.resize(400, 32)
        w.setText("https://{{host}}/api")
        w.set_variables({"host": "example.com"})
        # First "h" is in "https"; point inside {{host}}.
        w.fixed_cursor_index = w.text().index("{{host}}") + 2
        w.mouseMoveEvent(_mouse_move_event(w, QPoint(10, 16)))
        show_mock.assert_called_once()
        args, _kwargs = show_mock.call_args
        self.assertEqual(args[1], "example.com")

    @patch("pypost.ui.widgets.mixins.QToolTip.hideText")
    @patch("pypost.ui.widgets.mixins.QToolTip.showText")
    def test_mouse_over_plain_text_hides_tooltip(self, show_mock, hide_mock):
        w = _FixedCursorHoverLineEdit()
        w.resize(400, 32)
        w.setText("no variables here")
        w.set_variables({"x": "y"})
        w.fixed_cursor_index = 3
        w.mouseMoveEvent(_mouse_move_event(w, QPoint(10, 16)))
        show_mock.assert_not_called()
        hide_mock.assert_called()


class TestVariableAwarePlainTextEditTooltips(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    @patch("pypost.ui.widgets.mixins.QToolTip.hideText")
    @patch("pypost.ui.widgets.mixins.QToolTip.showText")
    def test_mouse_over_variable_in_body_shows_tooltip(self, show_mock, _hide):
        w = _FixedCursorHoverPlainText()
        w.resize(480, 120)
        body = '{\n  "u": "{{base}}/p"\n}'
        w.setPlainText(body)
        w.set_variables({"base": "https://api.example"})
        w.fixed_document_position = body.index("{{base}}") + 2
        w.mouseMoveEvent(_mouse_move_event(w, QPoint(20, 40)))
        show_mock.assert_called_once()
        self.assertEqual(show_mock.call_args[0][1], "https://api.example")

    @patch("pypost.ui.widgets.mixins.QToolTip.hideText")
    @patch("pypost.ui.widgets.mixins.QToolTip.showText")
    def test_mouse_over_plain_multiline_hides_tooltip(self, show_mock, hide_mock):
        w = _FixedCursorHoverPlainText()
        w.resize(200, 100)
        w.setPlainText("no {{here}} really")
        w.set_variables({"here": "x"})
        w.fixed_document_position = w.toPlainText().index("no ")
        w.mouseMoveEvent(_mouse_move_event(w, QPoint(5, 10)))
        show_mock.assert_not_called()
        hide_mock.assert_called()


if __name__ == "__main__":
    unittest.main()
