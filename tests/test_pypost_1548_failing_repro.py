"""Failing repro for PYPOST-1548.

With the hover limit requested, three synchronous viewport moves apply
hover feedback zero times until one processEvents, then once, for the
latest point. ``handle_click`` at that character toggles that span.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QPoint, Qt
from PySide6.QtGui import QMouseEvent, QTextCursor
from PySide6.QtWidgets import QApplication

from pypost.ui.widgets.foldable_code_view import FoldableCodeView
from pypost.ui.widgets.response_mask_controller import (
    MaskedTokenSpan,
    ResponseMaskController,
)

pytestmark = pytest.mark.timeout(30)

_PREFIX = "lead"
_MASK = "***"
_GAP = ".."
_TAIL = "tail"
_SPAN_COUNT = 2


def _build_document() -> tuple[str, list[MaskedTokenSpan]]:
    """Prefix, mask, gap, second mask, gap, and tail at count 2."""
    parts = [_PREFIX]
    spans: list[MaskedTokenSpan] = []
    cursor = len(_PREFIX)
    for index in range(_SPAN_COUNT):
        start = cursor
        end = start + len(_MASK)
        spans.append(
            MaskedTokenSpan(
                start_pos=start,
                end_pos=end,
                raw_value=f"value-{index}",
                masked_value=_MASK,
                path=f"field.{index}",
            )
        )
        parts.append(_MASK)
        parts.append(_GAP)
        cursor = end + len(_GAP)
    parts.append(_TAIL)
    return "".join(parts), spans


def _request_hover_limit(view: FoldableCodeView) -> ResponseMaskController:
    """Ask for the limit. Today's constructor has no such parameter.

    The stored flag is ignored until the coalesce exists, so the red
    failure is the hover count rather than ``TypeError``.
    """
    try:
        return ResponseMaskController(view, limit_hover_moves=True)
    except TypeError as exc:
        if "limit_hover_moves" not in str(exc):
            raise
        controller = ResponseMaskController(view)
        controller._limit_hover_moves = True
        return controller


def _character_positions(
    document_text: str,
    spans: list[MaskedTokenSpan],
    controller: ResponseMaskController,
) -> tuple[int, int, int]:
    """Span A, the gap miss, and span B. Inclusive end is still a hit."""
    assert len(_GAP) >= 2
    assert len(spans) == _SPAN_COUNT
    assert document_text.startswith(_PREFIX)
    assert document_text.endswith(_TAIL)
    span_a, span_b = spans
    assert span_a.start_pos == len(_PREFIX)
    assert document_text[span_a.start_pos:span_a.end_pos] == _MASK
    assert document_text[span_b.start_pos:span_b.end_pos] == _MASK
    assert span_b.start_pos - span_a.end_pos >= 2
    char_a = span_a.start_pos + 1
    char_gap = span_a.end_pos + 1
    char_b = span_b.start_pos + 1
    assert controller.span_at(char_a) is span_a
    assert controller.span_at(span_a.end_pos) is span_a
    assert controller.span_at(char_gap) is None
    assert controller.span_at(char_b) is span_b
    assert span_a.is_revealed is False
    assert span_b.is_revealed is False
    return char_a, char_gap, char_b


def _viewport_point(view: FoldableCodeView, char_pos: int) -> QPoint:
    """Center or an inset corner of ``cursorRect`` that maps back."""
    cursor = QTextCursor(view.document())
    cursor.setPosition(char_pos)
    rect = view.cursorRect(cursor)
    candidates = (
        rect.center(),
        rect.topLeft() + QPoint(1, 1),
        rect.topRight() + QPoint(-1, 1),
        rect.bottomLeft() + QPoint(1, -1),
        rect.bottomRight() + QPoint(-1, -1),
    )
    for point in candidates:
        if view.cursorForPosition(point).position() == char_pos:
            return point
    raise AssertionError(
        f"cursorRect candidates do not round-trip to character {char_pos}"
    )


def _mouse_move(local_pos: QPoint, global_pos: QPoint) -> QMouseEvent:
    return QMouseEvent(
        QEvent.Type.MouseMove,
        local_pos,
        global_pos,
        Qt.MouseButton.NoButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )


def _cleanup(view: FoldableCodeView, controller: ResponseMaskController) -> None:
    """Detach the viewport filter before closing to avoid teardown noise."""
    viewport = view.viewport()
    if viewport is not None:
        viewport.removeEventFilter(controller)
    controller.clear()
    view.close()


def test_enabled_hover_limit_coalesces_rapid_moves_and_keeps_latest_span(
    qapp: QApplication,
) -> None:
    """Three moves, then one processEvents, apply hover once at span B."""
    document_text, spans = _build_document()
    view = FoldableCodeView()
    view.setPlainText(document_text)
    controller = _request_hover_limit(view)
    controller.set_masked_spans(spans)
    try:
        assert controller._limit_hover_moves is True
        view.resize(800, 240)
        view.show()
        qapp.processEvents()
        char_a, char_gap, char_b = _character_positions(
            document_text, spans, controller
        )
        local_points = (
            _viewport_point(view, char_a),
            _viewport_point(view, char_gap),
            _viewport_point(view, char_b),
        )
        global_points = (QPoint(400, 10), QPoint(500, 20), QPoint(600, 30))
        assert len({(point.x(), point.y()) for point in global_points}) == 3
        viewport = view.viewport()
        show_target = (
            "pypost.ui.widgets.response_mask_controller.QToolTip.showText"
        )
        with (
            patch(show_target) as show_text,
            patch.object(viewport, "setCursor") as set_cursor,
        ):
            for local_pos, global_pos in zip(
                local_points, global_points, strict=True
            ):
                QCoreApplication.sendEvent(
                    viewport, _mouse_move(local_pos, global_pos)
                )
            assert show_text.call_count == 0 and set_cursor.call_count == 0, (
                "missing hover coalesce: three moves still applied hover "
                f"(showText={show_text.call_count}, "
                f"setCursor={set_cursor.call_count}); "
                "want 0 until one processEvents"
            )
            qapp.processEvents()
            assert show_text.call_count == 1
            assert show_text.call_args[0][0] == global_points[2]
            assert set_cursor.call_count == 1
            assert (
                set_cursor.call_args[0][0] == Qt.CursorShape.PointingHandCursor
            )
        assert controller.span_at(char_b) is spans[1]
        assert controller.handle_click(char_b) is True
        assert spans[1].is_revealed is True
        assert spans[0].is_revealed is False
        shown = view.toPlainText()
        assert shown[spans[0].start_pos:spans[0].end_pos] == _MASK
        assert spans[0].raw_value not in shown
        assert spans[1].raw_value in shown
    finally:
        _cleanup(view, controller)
