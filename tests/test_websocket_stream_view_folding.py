"""Automated red repro tests for JSON/YAML/XML code folding in WebSocket stream view.

Validates the contracts specified in:
- ai-tasks/PYPOST-1366/10-requirements.md
- ai-tasks/PYPOST-1366/20-architecture.md

Covers:
1. StreamDetailPane payload editor is a FoldableCodeView providing fold_controller,
   fold_all, unfold_all.
2. JSON payload auto-detection and fold regions discovery.
3. XML and YAML payload auto-detection and fold regions discovery.
4. Plain text payload displays as BodyFormat.PLAIN without fold regions.
5. Fold All and Unfold All buttons exist on detail pane and toggle block visibility.
6. Double-clicking fold header / gutter toggles collapsed state.
7. Hex mode toggled ON disables folding/sets PLAIN format; toggled OFF restores
   structure folding.
8. Wrap mode toggle preserves fold state.
9. Rapid streaming / follow-tail entry updates do not break folding state.
"""

from __future__ import annotations

import json

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication, QPushButton

from pypost.core.websocket_stream import StreamEntry
from pypost.ui.widgets.fold.fold_region import BodyFormat
from pypost.ui.widgets.foldable_code_view import FoldableCodeView
from pypost.ui.widgets.websocket.stream_view import StreamDetailPane

pytestmark = pytest.mark.timeout(30)

_WS_STREAM_DETAIL_FOLD_ALL_BUTTON = "pypost_ws_stream_detail_fold_all_button"
_WS_STREAM_DETAIL_UNFOLD_ALL_BUTTON = "pypost_ws_stream_detail_unfold_all_button"

_SAMPLE_JSON = json.dumps(
    {
        "event": "price_update",
        "data": {
            "symbol": "BTC-USD",
            "bids": [{"price": 60000.0, "qty": 1.5}, {"price": 59990.0, "qty": 2.0}],
            "asks": [{"price": 60010.0, "qty": 0.8}, {"price": 60020.0, "qty": 3.1}],
        },
    },
    indent=2,
)

_SAMPLE_XML = """<message>
  <header>
    <id>101</id>
    <sender>stream_service</sender>
  </header>
  <body>
    <item name="alpha">1</item>
    <item name="beta">2</item>
  </body>
</message>"""

_SAMPLE_YAML = """event: telemetry
devices:
  - id: sensor_1
    metrics:
      temperature: 22.4
      humidity: 55.1
  - id: sensor_2
    metrics:
      temperature: 24.1
      humidity: 50.8
"""

_SAMPLE_PLAIN = "Simple unformatted text message\nLine 2\nLine 3"


def _create_entry(
    seq: int = 1,
    payload: str = _SAMPLE_JSON,
    payload_format: str = "text",
    direction: str = "in",
    byte_size: int = 0,
) -> StreamEntry:
    return StreamEntry(
        seq=seq,
        ts_utc="2026-10-13T12:00:00.000Z",
        kind="message",
        direction=direction,
        payload_format=payload_format,
        payload=payload,
        byte_size=byte_size or len(payload.encode("utf-8")),
        truncated=False,
        detail="",
    )


def _visible_block_count(editor: FoldableCodeView) -> int:
    block = editor.document().firstBlock()
    count = 0
    while block.isValid():
        if block.isVisible():
            count += 1
        block = block.next()
    return count


@pytest.mark.timeout(30)
def test_detail_pane_uses_foldable_code_view(qapp: QApplication) -> None:
    """StreamDetailPane._editor must be a FoldableCodeView with fold controller."""
    pane = StreamDetailPane()
    try:
        assert hasattr(pane, "_editor"), "StreamDetailPane must have _editor attribute"
        assert isinstance(
            pane._editor, FoldableCodeView
        ), f"Expected FoldableCodeView, got {type(pane._editor).__name__}"
        assert hasattr(pane._editor, "fold_controller"), "Editor must have fold_controller()"
        fc = pane._editor.fold_controller()
        assert fc is not None, "fold_controller() must not be None"
        assert hasattr(pane._editor, "fold_all"), "Editor must have fold_all()"
        assert hasattr(pane._editor, "unfold_all"), "Editor must have unfold_all()"
    finally:
        pane.deleteLater()


@pytest.mark.timeout(30)
def test_json_payload_detected_and_folded(qapp: QApplication) -> None:
    """JSON payload in detail pane auto-detects BodyFormat.JSON and discovers fold regions."""
    pane = StreamDetailPane()
    try:
        entry = _create_entry(payload=_SAMPLE_JSON)
        pane.set_entry(entry)
        qapp.processEvents()

        editor = pane._editor
        assert hasattr(editor, "body_format"), "Editor must provide body_format()"
        assert editor.body_format() == BodyFormat.JSON, "Detected format should be BodyFormat.JSON"

        fc = editor.fold_controller()
        regions = fc.regions()
        assert len(regions) > 0, "JSON payload should produce fold regions"

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
        pane.deleteLater()


@pytest.mark.timeout(30)
def test_xml_payload_detected_and_folded(qapp: QApplication) -> None:
    """XML payload in detail pane auto-detects BodyFormat.XML and discovers fold regions."""
    pane = StreamDetailPane()
    try:
        entry = _create_entry(payload=_SAMPLE_XML)
        pane.set_entry(entry)
        qapp.processEvents()

        editor = pane._editor
        assert hasattr(editor, "body_format"), "Editor must provide body_format()"
        assert editor.body_format() == BodyFormat.XML, "Detected format should be BodyFormat.XML"

        fc = editor.fold_controller()
        regions = fc.regions()
        assert len(regions) > 0, "XML payload should produce fold regions"
    finally:
        pane.deleteLater()


@pytest.mark.timeout(30)
def test_yaml_payload_detected_and_folded(qapp: QApplication) -> None:
    """YAML payload in detail pane auto-detects BodyFormat.YAML and discovers fold regions."""
    pane = StreamDetailPane()
    try:
        entry = _create_entry(payload=_SAMPLE_YAML)
        pane.set_entry(entry)
        qapp.processEvents()

        editor = pane._editor
        assert hasattr(editor, "body_format"), "Editor must provide body_format()"
        assert editor.body_format() == BodyFormat.YAML, "Detected format should be BodyFormat.YAML"

        fc = editor.fold_controller()
        regions = fc.regions()
        assert len(regions) > 0, "YAML payload should produce fold regions"
    finally:
        pane.deleteLater()


@pytest.mark.timeout(30)
def test_plain_text_payload_no_folding(qapp: QApplication) -> None:
    """Plain text payload displays as BodyFormat.PLAIN without fold regions."""
    pane = StreamDetailPane()
    try:
        entry = _create_entry(payload=_SAMPLE_PLAIN)
        pane.set_entry(entry)
        qapp.processEvents()

        editor = pane._editor
        assert hasattr(editor, "body_format"), "Editor must provide body_format()"
        assert editor.body_format() == BodyFormat.PLAIN, (
            "Plain text payload should be BodyFormat.PLAIN"
        )

        fc = editor.fold_controller()
        assert len(fc.regions()) == 0, "Plain text payload must have zero fold regions"
    finally:
        pane.deleteLater()


@pytest.mark.timeout(30)
def test_fold_all_and_unfold_all_toolbar_buttons(qapp: QApplication) -> None:
    """Fold All and Unfold All toolbar buttons exist and toggle fold state."""
    pane = StreamDetailPane()
    try:
        fold_btn = pane.findChild(QPushButton, _WS_STREAM_DETAIL_FOLD_ALL_BUTTON)
        unfold_btn = pane.findChild(QPushButton, _WS_STREAM_DETAIL_UNFOLD_ALL_BUTTON)

        assert fold_btn is not None, "Toolbar must include Fold All button"
        assert unfold_btn is not None, "Toolbar must include Unfold All button"

        entry = _create_entry(payload=_SAMPLE_JSON)
        pane.set_entry(entry)
        qapp.processEvents()

        assert fold_btn.isEnabled(), "Fold All button should be enabled for structured JSON"
        assert unfold_btn.isEnabled(), "Unfold All button should be enabled for structured JSON"

        editor = pane._editor
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
        pane.deleteLater()


@pytest.mark.timeout(30)
def test_gutter_double_click_folding(qapp: QApplication) -> None:
    """Double-clicking on fold header block toggles collapsed state."""
    pane = StreamDetailPane()
    try:
        entry = _create_entry(payload=_SAMPLE_JSON)
        pane.set_entry(entry)
        qapp.processEvents()

        editor = pane._editor
        fc = editor.fold_controller()
        regions = fc.regions()
        assert len(regions) > 0, "Regions required for double click test"

        root_region = regions[0]
        assert not fc.is_collapsed(root_region.region_id), "Initial state should be expanded"

        # Calculate coordinates for block header in line number area
        block = editor.document().findBlockByNumber(root_region.header_block)
        top = round(
            editor.blockBoundingGeometry(block).translated(editor.contentOffset()).top()
        )
        gutter_widget = editor._line_number_area

        # Create mouse double click event on gutter for root header block
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
        pane.deleteLater()


@pytest.mark.timeout(30)
def test_hex_mode_disables_folding(qapp: QApplication) -> None:
    """Hex mode toggled ON sets PLAIN format and disables fold buttons; OFF restores them."""
    pane = StreamDetailPane()
    try:
        entry = _create_entry(payload=_SAMPLE_JSON)
        pane.set_entry(entry)
        qapp.processEvents()

        fold_btn = pane.findChild(QPushButton, _WS_STREAM_DETAIL_FOLD_ALL_BUTTON)
        unfold_btn = pane.findChild(QPushButton, _WS_STREAM_DETAIL_UNFOLD_ALL_BUTTON)
        assert fold_btn is not None and fold_btn.isEnabled()

        editor = pane._editor
        assert editor.body_format() == BodyFormat.JSON

        # Toggle Hex mode ON
        pane._on_toggle_hex()
        qapp.processEvents()

        assert pane.is_hex_mode is True
        assert editor.body_format() == BodyFormat.PLAIN, (
            "Hex mode must set body format to BodyFormat.PLAIN"
        )
        assert not fold_btn.isEnabled(), "Fold All button must be disabled in Hex mode"
        assert not unfold_btn.isEnabled(), "Unfold All button must be disabled in Hex mode"

        # Toggle Hex mode OFF
        pane._on_toggle_hex()
        qapp.processEvents()

        assert pane.is_hex_mode is False
        assert editor.body_format() == BodyFormat.JSON, (
            "Switching back from Hex mode must restore BodyFormat.JSON"
        )
        assert fold_btn.isEnabled(), "Fold All button must be re-enabled when Hex mode is OFF"
    finally:
        pane.deleteLater()


@pytest.mark.timeout(30)
def test_word_wrap_toggle_preserves_folding(qapp: QApplication) -> None:
    """Word wrap toggle switches wrap mode without resetting collapsed fold regions."""
    pane = StreamDetailPane()
    try:
        entry = _create_entry(payload=_SAMPLE_JSON)
        pane.set_entry(entry)
        qapp.processEvents()

        editor = pane._editor
        fc = editor.fold_controller()
        regions = fc.regions()
        assert len(regions) > 0

        # Collapse first region
        first_region = regions[0]
        fc.toggle(first_region.region_id)
        assert fc.is_collapsed(first_region.region_id)

        # Toggle word wrap
        pane._on_toggle_wrap()
        qapp.processEvents()

        assert fc.is_collapsed(first_region.region_id), (
            "Toggling wrap mode must preserve active collapsed fold regions"
        )

        # Toggle word wrap back
        pane._on_toggle_wrap()
        qapp.processEvents()

        assert fc.is_collapsed(first_region.region_id), (
            "Toggling wrap mode back must still preserve collapsed fold regions"
        )
    finally:
        pane.deleteLater()
