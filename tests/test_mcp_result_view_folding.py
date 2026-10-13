"""Tests for code folding support in McpResultView (PYPOST-1367).

Validates:
1. McpResultView embeds FoldableCodeView as _body (or provides fold_controller()).
2. JSON tool execution payload auto-detects BodyFormat.JSON and generates fold regions.
3. XML tool execution payload auto-detects BodyFormat.XML and generates fold regions.
4. YAML tool execution payload auto-detects BodyFormat.YAML and generates fold regions.
5. Plain text or unstructured tool execution payload sets BodyFormat.PLAIN without fold regions.
6. Fold All and Unfold All buttons exist (MCP_CLIENT_RESULT_FOLD_ALL_BUTTON,
   MCP_CLIENT_RESULT_UNFOLD_ALL_BUTTON) and toggle collapsed states.
7. Double-clicking fold header in gutter toggles collapsed state.
8. Error results (set_error or is_error=True) set BodyFormat.PLAIN and disable folding buttons.
9. set_in_progress() and clear() reset text and folding state.
"""

from __future__ import annotations

import json

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication, QPushButton

from pypost.ui.widget_ids import MCP_CLIENT_RESULT_PANE
from pypost.ui.widgets.fold.fold_region import BodyFormat
from pypost.ui.widgets.foldable_code_view import FoldableCodeView
from pypost.ui.widgets.mcp_client.mcp_result_view import McpResultView

pytestmark = pytest.mark.timeout(30)

MCP_CLIENT_RESULT_FOLD_ALL_BUTTON = "pypost_mcp_client_result_fold_all_button"
MCP_CLIENT_RESULT_UNFOLD_ALL_BUTTON = "pypost_mcp_client_result_unfold_all_button"

_SAMPLE_JSON_PAYLOAD = {
    "content": [
        {
            "type": "text",
            "text": json.dumps(
                {
                    "status": "success",
                    "items": [
                        {"id": 1, "name": "Alpha"},
                        {"id": 2, "name": "Beta"},
                    ],
                },
                indent=2,
            ),
        }
    ]
}

_SAMPLE_XML_PAYLOAD = {
    "content": [
        {
            "type": "text",
            "text": """<response>
  <data>
    <item id="1">Alpha</item>
    <item id="2">Beta</item>
  </data>
</response>""",
        }
    ]
}

_SAMPLE_YAML_PAYLOAD = {
    "content": [
        {
            "type": "text",
            "text": """version: "1.0"
services:
  database:
    image: postgres:16
    ports:
      - "5432:5432"
""",
        }
    ]
}

_SAMPLE_PLAIN_PAYLOAD = {
    "content": [
        {
            "type": "text",
            "text": "Task finished successfully in 4 steps.\nNo structured output provided.",
        }
    ]
}


def _visible_block_count(editor: FoldableCodeView) -> int:
    block = editor.document().firstBlock()
    count = 0
    while block.isValid():
        if block.isVisible():
            count += 1
        block = block.next()
    return count


@pytest.mark.timeout(30)
def test_mcp_result_view_uses_foldable_code_view(qapp: QApplication) -> None:
    """McpResultView._body must be a FoldableCodeView with fold controller."""
    view = McpResultView()
    try:
        assert hasattr(view, "_body"), "McpResultView must have _body attribute"
        assert isinstance(
            view._body, FoldableCodeView
        ), f"Expected FoldableCodeView, got {type(view._body).__name__}"
        assert view._body.objectName() == MCP_CLIENT_RESULT_PANE
        assert hasattr(view._body, "fold_controller"), "Body must provide fold_controller()"
        fc = view._body.fold_controller()
        assert fc is not None, "fold_controller() must not be None"
        assert hasattr(view._body, "fold_all"), "Body must provide fold_all()"
        assert hasattr(view._body, "unfold_all"), "Body must provide unfold_all()"
    finally:
        view.deleteLater()


@pytest.mark.timeout(30)
def test_json_mcp_result_detected_and_folded(qapp: QApplication) -> None:
    """JSON MCP tool result detects BodyFormat.JSON and discovers fold regions."""
    view = McpResultView()
    try:
        view.set_result(_SAMPLE_JSON_PAYLOAD, elapsed_s=0.15, is_error=False)
        qapp.processEvents()

        editor = view._body
        assert hasattr(editor, "body_format"), "Body must provide body_format()"
        assert editor.body_format() == BodyFormat.JSON, "Detected format should be BodyFormat.JSON"

        fc = editor.fold_controller()
        regions = fc.regions()
        assert len(regions) > 0, "JSON result should produce fold regions"

        total_blocks = editor.document().blockCount()
        assert _visible_block_count(editor) == total_blocks

        editor.fold_all()
        qapp.processEvents()
        visible_after_fold = _visible_block_count(editor)
        assert visible_after_fold < total_blocks, "fold_all() should collapse blocks"

        editor.unfold_all()
        qapp.processEvents()
        assert _visible_block_count(editor) == total_blocks, "unfold_all() should restore blocks"
    finally:
        view.deleteLater()


@pytest.mark.timeout(30)
def test_yaml_and_xml_mcp_results_folding(qapp: QApplication) -> None:
    """XML and YAML MCP tool results detect formats and create fold regions."""
    view = McpResultView()
    try:
        # Test XML result
        view.set_result(_SAMPLE_XML_PAYLOAD, elapsed_s=0.2, is_error=False)
        qapp.processEvents()

        editor = view._body
        assert hasattr(editor, "body_format"), "Body must provide body_format()"
        assert editor.body_format() == BodyFormat.XML, "Detected format should be BodyFormat.XML"
        assert len(editor.fold_controller().regions()) > 0, "XML result must produce fold regions"

        # Test YAML result
        view.set_result(_SAMPLE_YAML_PAYLOAD, elapsed_s=0.25, is_error=False)
        qapp.processEvents()

        assert editor.body_format() == BodyFormat.YAML, "Detected format should be BodyFormat.YAML"
        assert len(editor.fold_controller().regions()) > 0, "YAML result must produce fold regions"
    finally:
        view.deleteLater()


@pytest.mark.timeout(30)
def test_plain_and_unstructured_mcp_results_no_folding(qapp: QApplication) -> None:
    """Plain text or unstructured MCP results set BodyFormat.PLAIN without fold regions."""
    view = McpResultView()
    try:
        view.set_result(_SAMPLE_PLAIN_PAYLOAD, elapsed_s=0.05, is_error=False)
        qapp.processEvents()

        editor = view._body
        assert hasattr(editor, "body_format"), "Body must provide body_format()"
        assert editor.body_format() == BodyFormat.PLAIN, (
            "Unstructured text should be BodyFormat.PLAIN"
        )
        assert len(editor.fold_controller().regions()) == 0, (
            "Plain text result must have zero fold regions"
        )
    finally:
        view.deleteLater()


@pytest.mark.timeout(30)
def test_fold_all_and_unfold_all_buttons(qapp: QApplication) -> None:
    """Fold All and Unfold All toolbar buttons exist on McpResultView and toggle fold state."""
    view = McpResultView()
    try:
        fold_btn = view.findChild(QPushButton, MCP_CLIENT_RESULT_FOLD_ALL_BUTTON)
        unfold_btn = view.findChild(QPushButton, MCP_CLIENT_RESULT_UNFOLD_ALL_BUTTON)

        assert fold_btn is not None, "McpResultView must include Fold All button"
        assert unfold_btn is not None, "McpResultView must include Unfold All button"

        view.set_result(_SAMPLE_JSON_PAYLOAD, elapsed_s=0.1, is_error=False)
        qapp.processEvents()

        assert fold_btn.isEnabled(), "Fold All button should be enabled for structured JSON"
        assert unfold_btn.isEnabled(), "Unfold All button should be enabled for structured JSON"

        editor = view._body
        total_blocks = editor.document().blockCount()
        assert _visible_block_count(editor) == total_blocks

        fold_btn.click()
        qapp.processEvents()
        assert _visible_block_count(editor) < total_blocks, (
            "Clicking Fold All button must collapse blocks"
        )

        unfold_btn.click()
        qapp.processEvents()
        assert _visible_block_count(editor) == total_blocks, (
            "Clicking Unfold All button must expand all blocks"
        )
    finally:
        view.deleteLater()


@pytest.mark.timeout(30)
def test_gutter_double_click_folding(qapp: QApplication) -> None:
    """Double-clicking fold header in gutter toggles collapsed state."""
    view = McpResultView()
    try:
        view.set_result(_SAMPLE_JSON_PAYLOAD, elapsed_s=0.1, is_error=False)
        qapp.processEvents()

        editor = view._body
        fc = editor.fold_controller()
        regions = fc.regions()
        assert len(regions) > 0, "Regions required for double click test"

        root_region = regions[0]
        assert not fc.is_collapsed(root_region.region_id), "Initial state should be expanded"

        block = editor.document().findBlockByNumber(root_region.header_block)
        top = round(
            editor.blockBoundingGeometry(block).translated(editor.contentOffset()).top()
        )
        gutter_widget = editor._line_number_area

        # Send mouse double click event on gutter for root header block
        event = QMouseEvent(
            QMouseEvent.Type.MouseButtonDblClick,
            QPoint(5, top + 4),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        gutter_widget.mouseDoubleClickEvent(event)
        qapp.processEvents()

        assert fc.is_collapsed(root_region.region_id), (
            "Double-clicking fold header in gutter must toggle collapsed state"
        )

        # Double click again to expand
        event2 = QMouseEvent(
            QMouseEvent.Type.MouseButtonDblClick,
            QPoint(5, top + 4),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        gutter_widget.mouseDoubleClickEvent(event2)
        qapp.processEvents()

        assert not fc.is_collapsed(root_region.region_id), (
            "Double-clicking fold header again must expand region"
        )
    finally:
        view.deleteLater()


@pytest.mark.timeout(30)
def test_error_result_displays_plain_text(qapp: QApplication) -> None:
    """Error results set BodyFormat.PLAIN and disable fold buttons."""
    view = McpResultView()
    try:
        fold_btn = view.findChild(QPushButton, MCP_CLIENT_RESULT_FOLD_ALL_BUTTON)
        unfold_btn = view.findChild(QPushButton, MCP_CLIENT_RESULT_UNFOLD_ALL_BUTTON)

        # set_error() path
        view.set_error("Connection refused: tool execution failed", elapsed_s=0.05)
        qapp.processEvents()

        editor = view._body
        assert editor.body_format() == BodyFormat.PLAIN
        assert len(editor.fold_controller().regions()) == 0
        if fold_btn is not None:
            assert not fold_btn.isEnabled()
        if unfold_btn is not None:
            assert not unfold_btn.isEnabled()

        # is_error=True path with JSON payload
        view.set_result(_SAMPLE_JSON_PAYLOAD, elapsed_s=0.1, is_error=True)
        qapp.processEvents()

        # Even with error text, plain format or error handling applies
        assert "Error" in editor.toPlainText()
    finally:
        view.deleteLater()


@pytest.mark.timeout(30)
def test_clear_and_in_progress_resets_folding(qapp: QApplication) -> None:
    """Calling set_in_progress() or clear() empties text, resets format, and disables buttons."""
    view = McpResultView()
    try:
        fold_btn = view.findChild(QPushButton, MCP_CLIENT_RESULT_FOLD_ALL_BUTTON)
        unfold_btn = view.findChild(QPushButton, MCP_CLIENT_RESULT_UNFOLD_ALL_BUTTON)

        # First load structured content
        view.set_result(_SAMPLE_JSON_PAYLOAD, elapsed_s=0.1, is_error=False)
        qapp.processEvents()
        editor = view._body
        assert editor.body_format() == BodyFormat.JSON

        # Call set_in_progress()
        view.set_in_progress()
        qapp.processEvents()
        assert editor.toPlainText() == ""
        assert editor.body_format() == BodyFormat.PLAIN
        if fold_btn is not None:
            assert not fold_btn.isEnabled()
        if unfold_btn is not None:
            assert not unfold_btn.isEnabled()

        # Load content again and call clear()
        view.set_result(_SAMPLE_JSON_PAYLOAD, elapsed_s=0.1, is_error=False)
        qapp.processEvents()
        assert editor.body_format() == BodyFormat.JSON

        view.clear()
        qapp.processEvents()
        assert editor.toPlainText() == ""
        assert editor.body_format() == BodyFormat.PLAIN
        if fold_btn is not None:
            assert not fold_btn.isEnabled()
        if unfold_btn is not None:
            assert not unfold_btn.isEnabled()
    finally:
        view.deleteLater()


@pytest.mark.timeout(30)
def test_mcp_result_view_debug_logging(
    qapp: QApplication, caplog: pytest.LogCaptureFixture
) -> None:
    """McpResultView logs format detection and fold/unfold actions at DEBUG level."""
    import logging

    view = McpResultView()
    try:
        with caplog.at_level(
            logging.DEBUG, logger="pypost.ui.widgets.mcp_client.mcp_result_view"
        ):
            view.set_result(_SAMPLE_JSON_PAYLOAD, elapsed_s=0.1, is_error=False)
            qapp.processEvents()
            view.fold_all()
            qapp.processEvents()
            view.unfold_all()
            qapp.processEvents()

        messages = [
            r.message
            for r in caplog.records
            if r.name == "pypost.ui.widgets.mcp_client.mcp_result_view"
        ]
        assert any("mcp_result_folding_format_detected format=JSON" in m for m in messages)
        assert any("mcp_result_folding_fold_all_invoked" in m for m in messages)
        assert any("mcp_result_folding_unfold_all_invoked" in m for m in messages)
        # Verify no raw payload string or JSON structure leaked into debug log messages
        assert not any("Alpha" in m for m in messages)
    finally:
        view.deleteLater()
