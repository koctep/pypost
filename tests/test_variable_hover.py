"""Variable hover tests (PYPOST-117–121, PYPOST-130–133).

PYPOST-117 / PYPOST-121: VariableHoverHelper + VariableHoverMixin for URL/body fields
(VariableAwarePlainTextEdit / VariableAwareLineEdit).

PYPOST-118: QToolTip + LineEdit (fixed cursor) contract.

PYPOST-130 / PYPOST-133: resolve_text edge cases (batch 2 / PYPOST-15 path).

PYPOST-131: QToolTip + PlainTextEdit (JSON body) contract, same mixin as CodeEditor body.
"""

import pytest

pytestmark = pytest.mark.timeout(60)

import unittest
from typing import Tuple
from unittest.mock import MagicMock, patch

from PySide6.QtCore import QEvent, QPoint, Qt
from PySide6.QtGui import QMouseEvent, QTextCursor
from PySide6.QtWidgets import QApplication, QLineEdit, QPlainTextEdit, QTableWidgetItem

from pypost.core.constants import HIDDEN_MASK
from pypost.core.template_expression_tokenizer import (
    TEMPLATE_PLACEHOLDER_PATTERN,
    tokenize_template_expressions,
)
from pypost.ui.widgets.mixins import (
    VariableHoverHelper,
    VariableHoverLocator,
    VariableHoverMixin,
    VariableHoverResolver,
)
from pypost.ui.widgets.variable_aware_widgets import VariableAwareTableWidget


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
        self._hover_line_scoped_scan = True
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


class _FixedHoverTableWidget(VariableAwareTableWidget):
    """Table widget with deterministic itemAt behavior for hover tests."""

    def __init__(self) -> None:
        super().__init__(1, 1)
        self._item_for_hover = None

    def set_hover_text(self, text: str) -> None:
        self._item_for_hover = QTableWidgetItem(text)

    def clear_hover_item(self) -> None:
        self._item_for_hover = None

    def itemAt(self, pos):  # noqa: ARG002
        return self._item_for_hover


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

    def test_find_expression_at_index_for_variant_b_function(self):
        text = "x{{urlencode(db)}}y"
        idx = text.index("urlencode")
        self.assertEqual(
            VariableHoverHelper.find_expression_at_index(text, idx),
            "{{urlencode(db)}}",
        )

    def test_expression_pattern_matches_core_tokenizer(self):
        text = "{{ a }} {{ md5(urlencode(db)) }}"
        hover_tokens = [
            match.group(0)
            for match in VariableHoverHelper.EXPRESSION_PATTERN.finditer(text)
        ]
        inner_tokens = tokenize_template_expressions(text)
        self.assertEqual(
            hover_tokens,
            [
                match.group(0)
                for match in TEMPLATE_PLACEHOLDER_PATTERN.finditer(text)
            ],
        )
        self.assertEqual(
            [match.group(1) for match in TEMPLATE_PLACEHOLDER_PATTERN.finditer(text)],
            inner_tokens,
        )

    def test_find_expression_at_index_for_nested_function(self):
        text = "x{{ md5(urlencode(db)) }}y"
        idx = text.index("md5")
        self.assertEqual(
            VariableHoverHelper.find_expression_at_index(text, idx),
            "{{ md5(urlencode(db)) }}",
        )

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

    def test_get_variable_value_one_level_chain(self):
        self.assertEqual(
            VariableHoverHelper.get_variable_value(
                "a",
                {"a": "{{b}}", "b": "resolved"},
            ),
            "resolved",
        )

    def test_get_variable_value_multi_level_chain(self):
        self.assertEqual(
            VariableHoverHelper.get_variable_value(
                "a",
                {"a": "{{b}}", "b": "{{c}}", "c": "deep"},
            ),
            "deep",
        )

    def test_get_variable_value_cycle_returns_unresolved_reference(self):
        self.assertEqual(
            VariableHoverHelper.get_variable_value(
                "a",
                {"a": "{{b}}", "b": "{{a}}"},
            ),
            "{{a}}",
        )

    def test_get_variable_value_self_cycle_returns_reference(self):
        self.assertEqual(
            VariableHoverHelper.get_variable_value(
                "loop",
                {"loop": "{{loop}}"},
            ),
            "{{loop}}",
        )

    def test_get_variable_value_chain_stops_at_max_depth(self):
        variables = {
            "v0": "{{v1}}",
            "v1": "{{v2}}",
            "v2": "{{v3}}",
            "v3": "leaf",
        }
        with patch(
            "pypost.ui.widgets.mixins.TOOLTIP_REFERENCE_MAX_DEPTH",
            2,
        ):
            self.assertEqual(
                VariableHoverHelper.get_variable_value("v0", variables),
                "{{v3}}",
            )

    def test_get_variable_value_chain_hidden_inner_returns_mask(self):
        self.assertEqual(
            VariableHoverHelper.get_variable_value(
                "a",
                {"a": "{{secret}}", "secret": "value"},
                {"secret"},
            ),
            HIDDEN_MASK,
        )

    def test_resolve_text_one_level_chain(self):
        out = VariableHoverHelper.resolve_text(
            "{{a}}",
            {"a": "{{b}}", "b": "ok"},
        )
        self.assertEqual(out, "ok")

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

    def test_resolve_text_variant_b_function_uses_runtime_resolution(self):
        out = VariableHoverHelper.resolve_text(
            "db={{urlencode(db)}}",
            {"db": "a b/c"},
        )
        self.assertEqual(out, "db=a%20b%2Fc")

    def test_resolve_text_invalid_variant_b_function_keeps_token(self):
        out = VariableHoverHelper.resolve_text(
            "x={{not_allowed(db)}}",
            {"db": "a"},
        )
        self.assertEqual(out, "x={{not_allowed(db)}}")

    def test_slice_line_at_index_middle_of_line(self):
        text = "line0\n  {{var}} here\nline2"
        idx = text.index("var")
        line_text, line_idx = VariableHoverMixin._slice_line_at_index(text, idx)
        self.assertEqual(line_text, "  {{var}} here")
        self.assertEqual(line_idx, line_text.index("var"))

    def test_slice_line_at_index_first_line(self):
        text = "{{top}}\nsecond"
        idx = text.index("top")
        line_text, line_idx = VariableHoverMixin._slice_line_at_index(text, idx)
        self.assertEqual(line_text, "{{top}}")
        self.assertEqual(line_idx, 2)

    def test_resolve_text_variant_b_function_marks_hover_render_path(self):
        original_service = VariableHoverHelper._template_service
        try:
            fake_service = MagicMock()
            fake_service.render_string.return_value = "resolved"
            VariableHoverHelper._template_service = fake_service
            out = VariableHoverHelper.resolve_text("{{urlencode(db)}}", {"db": "a b"})
            self.assertEqual(out, "resolved")
            fake_service.render_string.assert_called_once_with(
                "{{urlencode(db)}}", {"db": "a b"}, render_path="hover",
            )
        finally:
            VariableHoverHelper._template_service = original_service


class TestVariableHoverSplit(unittest.TestCase):
    """PYPOST-129: locator vs resolver responsibilities."""

    def test_locator_finds_plain_variable(self):
        text = "x{{foo}}y"
        idx = text.index("f")
        self.assertEqual(
            VariableHoverLocator.find_variable_at_index(text, idx),
            "foo",
        )

    def test_locator_finds_expression_token(self):
        text = "x{{urlencode(db)}}y"
        idx = text.index("urlencode")
        self.assertEqual(
            VariableHoverLocator.find_expression_at_index(text, idx),
            "{{urlencode(db)}}",
        )

    def test_resolver_resolve_text_plain(self):
        out = VariableHoverResolver.resolve_text("{{a}}", {"a": "v"})
        self.assertEqual(out, "v")

    def test_helper_facade_matches_split_classes(self):
        text = "{{x}}"
        variables = {"x": "ok"}
        self.assertEqual(
            VariableHoverHelper.find_expression_at_index(text, 1),
            VariableHoverLocator.find_expression_at_index(text, 1),
        )
        self.assertEqual(
            VariableHoverHelper.resolve_text(text, variables),
            VariableHoverResolver.resolve_text(text, variables),
        )

    def test_template_service_alias_shared(self):
        original = VariableHoverHelper._template_service
        try:
            fake = MagicMock()
            VariableHoverHelper._template_service = fake
            self.assertIs(VariableHoverResolver._template_service(), fake)
        finally:
            VariableHoverHelper._template_service = original


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

    @patch("pypost.ui.widgets.mixins.QToolTip.hideText")
    @patch("pypost.ui.widgets.mixins.QToolTip.showText")
    def test_mouse_over_variant_b_function_shows_runtime_value(self, show_mock, _hide):
        w = _FixedCursorHoverLineEdit()
        w.resize(400, 32)
        w.setText("https://{{urlencode(path)}}")
        w.set_variables({"path": "a b/c"})
        w.fixed_cursor_index = w.text().index("urlencode")
        w.mouseMoveEvent(_mouse_move_event(w, QPoint(10, 16)))
        show_mock.assert_called_once()
        self.assertEqual(show_mock.call_args[0][1], "a%20b%2Fc")


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

    @patch("pypost.ui.widgets.mixins.QToolTip.hideText")
    @patch("pypost.ui.widgets.mixins.QToolTip.showText")
    def test_line_scoped_scan_finds_variable_on_deep_line(self, show_mock, _hide):
        w = _FixedCursorHoverPlainText()
        w.resize(480, 400)
        filler = "\n".join(f'{{"k{i}": "plain{i}"}}' for i in range(200))
        target_line = '  "url": "{{deep}}"'
        body = f"{filler}\n{target_line}\n{filler}"
        w.setPlainText(body)
        w.set_variables({"deep": "found"})
        w.fixed_document_position = body.index("{{deep}}") + 2
        w.mouseMoveEvent(_mouse_move_event(w, QPoint(20, 200)))
        show_mock.assert_called_once()
        self.assertEqual(show_mock.call_args[0][1], "found")

    @patch("pypost.ui.widgets.mixins.QToolTip.hideText")
    @patch("pypost.ui.widgets.mixins.QToolTip.showText")
    def test_mouse_over_variant_b_function_in_body_shows_runtime_value(
        self, show_mock, _hide,
    ):
        w = _FixedCursorHoverPlainText()
        w.resize(480, 120)
        body = '{\n  "p": "{{base64(path)}}"\n}'
        w.setPlainText(body)
        w.set_variables({"path": "hello"})
        w.fixed_document_position = body.index("base64")
        w.mouseMoveEvent(_mouse_move_event(w, QPoint(20, 40)))
        show_mock.assert_called_once()
        self.assertEqual(show_mock.call_args[0][1], "aGVsbG8=")


class TestVariableAwareTableWidgetTooltips(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    @patch("pypost.ui.widgets.variable_aware_widgets.QToolTip.hideText")
    @patch("pypost.ui.widgets.variable_aware_widgets.QToolTip.showText")
    def test_mouse_over_variant_b_function_in_table_cell_shows_runtime_value(
        self, show_mock, _hide,
    ):
        w = _FixedHoverTableWidget()
        w.resize(300, 100)
        w.set_hover_text("{{base64(path)}}")
        w.set_variables({"path": "hello"})
        w.mouseMoveEvent(_mouse_move_event(w, QPoint(10, 10)))
        show_mock.assert_called_once()
        self.assertEqual(show_mock.call_args[0][1], "aGVsbG8=")

    @patch("pypost.ui.widgets.variable_aware_widgets.QToolTip.hideText")
    @patch("pypost.ui.widgets.variable_aware_widgets.QToolTip.showText")
    def test_mouse_over_plain_table_cell_hides_tooltip(self, show_mock, hide_mock):
        w = _FixedHoverTableWidget()
        w.resize(300, 100)
        w.set_hover_text("plain text")
        w.set_variables({"path": "hello"})
        w.mouseMoveEvent(_mouse_move_event(w, QPoint(10, 10)))
        show_mock.assert_not_called()
        hide_mock.assert_called()


if __name__ == "__main__":
    unittest.main()
