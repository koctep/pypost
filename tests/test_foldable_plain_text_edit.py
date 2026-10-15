"""Tests for FoldablePlainTextEdit base class and unified folding contract (PYPOST-1369).

Asserts class hierarchy, shared gutter/folding API contract across FoldableCodeView
and CodeEditor, gutter double-click fold toggling on CodeEditor, and direct
behavior of FoldablePlainTextEdit.
"""

from __future__ import annotations

import json
import logging

import pytest
from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QMouseEvent, QPaintEvent
from PySide6.QtWidgets import QApplication, QPlainTextEdit

from pypost.ui.widgets.code_editor import CodeEditor
from pypost.ui.widgets.fold import BodyFormat
from pypost.ui.widgets.foldable_code_view import FoldableCodeView
from pypost.ui.widgets.line_number_area import LineNumberArea

pytestmark = pytest.mark.timeout(30)

_SAMPLE_JSON = json.dumps(
    {"users": [{"id": 1, "name": "Ada"}, {"id": 2, "name": "Bob"}]},
    indent=2,
)


def test_foldable_plain_text_edit_class_hierarchy() -> None:
    """FoldableCodeView and CodeEditor must inherit from FoldablePlainTextEdit."""
    from pypost.ui.widgets.foldable_plain_text_edit import FoldablePlainTextEdit

    assert issubclass(FoldablePlainTextEdit, QPlainTextEdit), (
        "FoldablePlainTextEdit must subclass QPlainTextEdit directly"
    )
    assert issubclass(FoldableCodeView, FoldablePlainTextEdit), (
        "FoldableCodeView must subclass FoldablePlainTextEdit"
    )
    assert issubclass(CodeEditor, FoldablePlainTextEdit), (
        "CodeEditor must subclass FoldablePlainTextEdit"
    )


@pytest.mark.parametrize("widget_cls", [FoldableCodeView, CodeEditor])
def test_unified_folding_contract_methods_exist(widget_cls: type) -> None:
    """Both FoldableCodeView and CodeEditor must expose the common folding interface."""
    required_methods = [
        "fold_controller",
        "body_format",
        "set_body_format",
        "line_number_area_width",
        "chevron_width",
        "line_number_area_paint_event",
        "line_number_area_mouse_press",
        "line_number_area_mouse_double_click",
        "fold_all",
        "unfold_all",
        "reveal_block",
    ]
    for method_name in required_methods:
        assert hasattr(widget_cls, method_name), (
            f"{widget_cls.__name__} must implement {method_name}()"
        )


def test_code_editor_gutter_double_click_toggles_fold(qapp: QApplication) -> None:
    """Double-clicking a fold header in CodeEditor gutter toggles fold state."""
    editor = CodeEditor()
    try:
        editor.setPlainText(_SAMPLE_JSON)
        editor.fold_controller()._run_scan()
        regions = editor.fold_controller().regions()
        assert len(regions) > 0, "Nested JSON must produce at least one fold region"
        root = regions[0]
        assert not editor.fold_controller().is_collapsed(root.region_id), (
            "Initial region state must be expanded"
        )

        block = editor.document().findBlockByNumber(root.header_block)
        top = round(
            editor.blockBoundingGeometry(block).translated(editor.contentOffset()).top()
        )
        gutter_widget = editor._line_number_area

        # Double click on fold header line in gutter (outside chevron zone)
        event = QMouseEvent(
            QMouseEvent.Type.MouseButtonDblClick,
            QPoint(editor.line_number_area_width() - 2, top + 4),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        gutter_widget.mouseDoubleClickEvent(event)
        qapp.processEvents()

        assert editor.fold_controller().is_collapsed(root.region_id), (
            "Double-clicking fold header in CodeEditor gutter must collapse region"
        )

        # Double click again to expand
        event_expand = QMouseEvent(
            QMouseEvent.Type.MouseButtonDblClick,
            QPoint(editor.line_number_area_width() - 2, top + 4),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        gutter_widget.mouseDoubleClickEvent(event_expand)
        qapp.processEvents()

        assert not editor.fold_controller().is_collapsed(root.region_id), (
            "Double-clicking collapsed fold header in CodeEditor gutter must expand region"
        )
    finally:
        editor.deleteLater()


def test_code_editor_convenience_fold_methods(qapp: QApplication) -> None:
    """CodeEditor must support fold_all(), unfold_all(), and reveal_block()."""
    editor = CodeEditor()
    try:
        editor.setPlainText(_SAMPLE_JSON)
        editor.fold_controller()._run_scan()
        total_blocks = editor.document().blockCount()

        editor.fold_all()
        qapp.processEvents()
        visible_count = sum(
            1
            for i in range(total_blocks)
            if editor.document().findBlockByNumber(i).isVisible()
        )
        assert visible_count < total_blocks, "fold_all() should collapse blocks"

        editor.unfold_all()
        qapp.processEvents()
        visible_after_unfold = sum(
            1
            for i in range(total_blocks)
            if editor.document().findBlockByNumber(i).isVisible()
        )
        assert visible_after_unfold == total_blocks, (
            "unfold_all() should expand all blocks"
        )

        # Collapse again and test reveal_block
        editor.fold_all()
        qapp.processEvents()
        target_block = total_blocks - 2
        editor.reveal_block(target_block)
        assert editor.document().findBlockByNumber(target_block).isVisible(), (
            "reveal_block() should make target block visible"
        )
    finally:
        editor.deleteLater()


def test_foldable_plain_text_edit_direct_instantiation(qapp: QApplication) -> None:
    """FoldablePlainTextEdit can be instantiated directly and manages gutter and folding."""
    from pypost.ui.widgets.foldable_plain_text_edit import FoldablePlainTextEdit

    edit = FoldablePlainTextEdit()
    try:
        assert isinstance(edit._line_number_area, LineNumberArea)
        assert edit.chevron_width() == 14
        assert edit.body_format() == BodyFormat.PLAIN

        # Dynamic gutter width test: 1 line vs 100 lines
        w1 = edit.line_number_area_width()
        edit.setPlainText("\n".join(f"line {i}" for i in range(100)))
        w100 = edit.line_number_area_width()
        assert w100 > w1, "Gutter width must expand for larger line counts"

        # Enable JSON folding on base class
        edit.set_body_format(BodyFormat.JSON)
        edit.setPlainText(_SAMPLE_JSON)
        edit.fold_controller()._run_scan()
        regions = edit.fold_controller().regions()
        assert len(regions) > 0, (
            "FoldablePlainTextEdit must discover fold regions for JSON"
        )

        # Test fold_all and unfold_all
        total_blocks = edit.document().blockCount()
        edit.fold_all()
        visible_count = sum(
            1
            for i in range(total_blocks)
            if edit.document().findBlockByNumber(i).isVisible()
        )
        assert visible_count < total_blocks

        edit.unfold_all()
        assert (
            sum(
                1
                for i in range(total_blocks)
                if edit.document().findBlockByNumber(i).isVisible()
            )
            == total_blocks
        )

        # Test paint event execution without crashing
        rect = QRect(0, 0, edit.line_number_area_width(), 100)
        event = QPaintEvent(rect)
        edit.line_number_area_paint_event(event)
    finally:
        edit.deleteLater()


def test_foldable_plain_text_edit_gutter_clicks(qapp: QApplication) -> None:
    """FoldablePlainTextEdit handles single click on chevron and double click on header."""
    from pypost.ui.widgets.foldable_plain_text_edit import FoldablePlainTextEdit

    edit = FoldablePlainTextEdit()
    try:
        edit.set_body_format(BodyFormat.JSON)
        edit.setPlainText(_SAMPLE_JSON)
        edit.fold_controller()._run_scan()
        regions = edit.fold_controller().regions()
        assert len(regions) > 0
        root = regions[0]

        block = edit.document().findBlockByNumber(root.header_block)
        top = round(
            edit.blockBoundingGeometry(block).translated(edit.contentOffset()).top()
        )
        gutter = edit._line_number_area

        # Single click on chevron (x <= chevron_width)
        click_event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPoint(5, top + 4),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        gutter.mousePressEvent(click_event)
        assert edit.fold_controller().is_collapsed(root.region_id), (
            "Single click on chevron must collapse region"
        )

        # Single click on number area (x > chevron_width) should NOT toggle
        miss_event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPoint(edit.line_number_area_width() - 2, top + 4),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        gutter.mousePressEvent(miss_event)
        assert edit.fold_controller().is_collapsed(root.region_id), (
            "Single click outside chevron must not toggle region"
        )

        # Double click on number area (x > chevron_width) SHOULD toggle region
        dbl_event = QMouseEvent(
            QMouseEvent.Type.MouseButtonDblClick,
            QPoint(edit.line_number_area_width() - 2, top + 4),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        gutter.mouseDoubleClickEvent(dbl_event)
        assert not edit.fold_controller().is_collapsed(root.region_id), (
            "Double click anywhere on header line must expand region"
        )
    finally:
        edit.deleteLater()


def test_foldable_plain_text_edit_set_plain_text_expands_all(qapp: QApplication) -> None:
    """Calling setPlainText on FoldablePlainTextEdit expands all regions first."""
    from pypost.ui.widgets.foldable_plain_text_edit import FoldablePlainTextEdit

    edit = FoldablePlainTextEdit()
    try:
        edit.set_body_format(BodyFormat.JSON)
        edit.setPlainText(_SAMPLE_JSON)
        edit.fold_controller()._run_scan()
        edit.fold_all()

        # Set new text
        edit.setPlainText(_SAMPLE_JSON)
        edit.fold_controller()._run_scan()
        total_blocks = edit.document().blockCount()
        visible_count = sum(
            1
            for i in range(total_blocks)
            if edit.document().findBlockByNumber(i).isVisible()
        )
        assert visible_count == total_blocks, (
            "setPlainText must expand all regions before setting new content"
        )
    finally:
        edit.deleteLater()


def test_fold_interactions_structured_debug_logging(
    qapp: QApplication, caplog: pytest.LogCaptureFixture
) -> None:
    """Fold interactions emit structured debug logs without dumping payload text."""
    from pypost.ui.widgets.foldable_plain_text_edit import FoldablePlainTextEdit

    caplog.set_level(logging.DEBUG)

    edit = FoldablePlainTextEdit()
    try:
        edit.set_body_format(BodyFormat.JSON)
        assert any(
            "fold_body_format_changed widget=FoldablePlainTextEdit format=json" in record.message
            for record in caplog.records
        )

        edit.setPlainText(_SAMPLE_JSON)
        edit.fold_controller()._run_scan()
        regions = edit.fold_controller().regions()
        assert len(regions) > 0
        root = regions[0]

        block = edit.document().findBlockByNumber(root.header_block)
        top = round(
            edit.blockBoundingGeometry(block).translated(edit.contentOffset()).top()
        )
        gutter = edit._line_number_area

        caplog.clear()
        # Single click on chevron: chevron_click
        click_event = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPoint(5, top + 4),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        gutter.mousePressEvent(click_event)
        assert any(
            "fold_gutter_toggle widget=FoldablePlainTextEdit" in r.message
            and f"block={root.header_block}" in r.message
            and f"region_id={root.region_id}" in r.message
            and "toggle_type=chevron_click" in r.message
            for r in caplog.records
        )

        caplog.clear()
        # Double click on gutter: double_click
        dbl_event = QMouseEvent(
            QMouseEvent.Type.MouseButtonDblClick,
            QPoint(edit.line_number_area_width() - 2, top + 4),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        gutter.mouseDoubleClickEvent(dbl_event)
        assert any(
            "fold_gutter_toggle widget=FoldablePlainTextEdit" in r.message
            and "toggle_type=double_click" in r.message
            for r in caplog.records
        )

        caplog.clear()
        edit.fold_all()
        assert any(
            "fold_all_invoked widget=FoldablePlainTextEdit" in r.message
            for r in caplog.records
        )

        caplog.clear()
        edit.unfold_all()
        assert any(
            "unfold_all_invoked widget=FoldablePlainTextEdit" in r.message
            for r in caplog.records
        )

        caplog.clear()
        edit.reveal_block(root.header_block)
        assert any(
            f"reveal_block_invoked widget=FoldablePlainTextEdit block={root.header_block}"
            in r.message
            for r in caplog.records
        )

        # Ensure no raw JSON payload was logged
        for record in caplog.records:
            assert _SAMPLE_JSON not in record.message
    finally:
        edit.deleteLater()

    editor = CodeEditor()
    try:
        editor.setPlainText(_SAMPLE_JSON)
        editor.fold_controller()._run_scan()
        regions = editor.fold_controller().regions()
        root = regions[0]
        block = editor.document().findBlockByNumber(root.header_block)
        top = round(
            editor.blockBoundingGeometry(block).translated(editor.contentOffset()).top()
        )
        gutter = editor._line_number_area

        caplog.clear()
        dbl_event = QMouseEvent(
            QMouseEvent.Type.MouseButtonDblClick,
            QPoint(editor.line_number_area_width() - 2, top + 4),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        gutter.mouseDoubleClickEvent(dbl_event)
        assert any(
            "fold_gutter_toggle widget=CodeEditor" in r.message
            and "toggle_type=double_click" in r.message
            for r in caplog.records
        )
    finally:
        editor.deleteLater()
