"""Automated repro / regression suite for PYPOST-1390.

Locks inclusive ``span_at`` semantics against a linear oracle and asserts that
high-N hover-style hit-testing does logarithmic work (AC-1 / AC-5) under the
``bisect_right`` implementation.
"""

from __future__ import annotations

import json
import math
from typing import Sequence

import pytest
from PySide6.QtWidgets import QApplication

from pypost.ui.widgets.foldable_code_view import FoldableCodeView
from pypost.ui.widgets.response_mask_controller import (
    MaskedTokenSpan,
    ResponseMaskController,
    format_masked_json,
)

pytestmark = pytest.mark.timeout(30)

_SPAN_COUNT = 512


def _linear_span_at(
    spans: Sequence[MaskedTokenSpan],
    char_pos: int,
) -> MaskedTokenSpan | None:
    """Reference oracle: first inclusive hit in list order."""
    for span in spans:
        if span.start_pos <= char_pos <= span.end_pos:
            return span
    return None


def _synthetic_spans(count: int, gap: int = 2, width: int = 4) -> list[MaskedTokenSpan]:
    """Build ordered, non-overlapping spans with fixed gaps between them."""
    spans: list[MaskedTokenSpan] = []
    pos = 0
    for i in range(count):
        start = pos
        end = start + width
        spans.append(
            MaskedTokenSpan(
                start_pos=start,
                end_pos=end,
                raw_value=f'"raw-{i}"',
                masked_value='"***"',
                path=f"field{i}",
            )
        )
        pos = end + gap + 1
    return spans


def _make_controller(
    qapp: QApplication,
    spans: list[MaskedTokenSpan],
    document_text: str | None = None,
) -> tuple[FoldableCodeView, ResponseMaskController]:
    view = FoldableCodeView()
    if document_text is None:
        last_end = spans[-1].end_pos if spans else 0
        document_text = "x" * max(last_end + 8, 16)
    view.setPlainText(document_text)
    controller = ResponseMaskController(view)
    controller.set_masked_spans(spans)
    return view, controller


def _cleanup_controller(view: FoldableCodeView, controller: ResponseMaskController) -> None:
    """Detach the viewport filter before closing to avoid teardown eventFilter noise."""
    viewport = view.viewport()
    if viewport is not None:
        viewport.removeEventFilter(controller)
    controller.clear()
    view.close()


class _InstrumentedSpans(list):
    """List that counts per-element visits via iteration and integer indexing.

    Linear ``for span in self._spans`` increments on each yield; ``bisect_right``
    increments on each ``__getitem__`` probe (~log N).
    """

    def __init__(self, spans: Sequence[MaskedTokenSpan]) -> None:
        super().__init__(spans)
        self.item_visits = 0

    def __iter__(self):
        for item in list.__iter__(self):
            self.item_visits += 1
            yield item

    def __getitem__(self, index):  # type: ignore[override]
        item = list.__getitem__(self, index)
        if isinstance(index, int):
            self.item_visits += 1
        return item


def _parity_positions(spans: Sequence[MaskedTokenSpan]) -> list[int]:
    """Representative hit / miss / boundary positions for oracle parity."""
    positions = [-1, 0]
    for span in spans:
        positions.extend(
            [
                span.start_pos - 1,
                span.start_pos,
                (span.start_pos + span.end_pos) // 2,
                span.end_pos,
                span.end_pos + 1,
            ]
        )
    if spans:
        positions.append(spans[-1].end_pos + 10)
    return positions


def test_span_at_matches_linear_oracle_for_hits_misses_and_inclusive_ends(
    qapp: QApplication,
) -> None:
    """Semantic lock: hits, misses, empty, and inclusive endpoints match the oracle."""
    empty_view, empty_ctrl = _make_controller(qapp, [])
    try:
        assert empty_ctrl.span_at(0) is None
        assert empty_ctrl.span_at(42) is None
    finally:
        _cleanup_controller(empty_view, empty_ctrl)

    spans = _synthetic_spans(8, gap=3, width=5)
    view, controller = _make_controller(qapp, spans)
    try:
        for char_pos in _parity_positions(spans):
            assert controller.span_at(char_pos) is _linear_span_at(spans, char_pos), (
                f"span_at({char_pos}) diverged from linear oracle"
            )
        # Explicit inclusive-end freeze (FR-2 / NFR-2).
        first = spans[0]
        assert controller.span_at(first.start_pos) is first
        assert controller.span_at(first.end_pos) is first
        # Gap between first and second must miss.
        gap_pos = first.end_pos + 1
        assert gap_pos < spans[1].start_pos
        assert controller.span_at(gap_pos) is None
    finally:
        _cleanup_controller(view, controller)


def test_span_at_parity_holds_after_handle_click_shifts_later_spans(
    qapp: QApplication,
) -> None:
    """After toggle + later-span shift, span_at still matches the linear oracle."""
    payload = {"alpha": "secret-a", "beta": "secret-b", "gamma": "secret-c"}
    text, spans = format_masked_json(json.dumps(payload), hidden_fields=["alpha", "beta", "gamma"])
    assert len(spans) >= 3

    view, controller = _make_controller(qapp, spans, document_text=text)
    try:
        target = spans[0]
        assert controller.handle_click(target.start_pos) is True
        updated = controller.spans()
        assert updated[0].is_revealed is True
        for char_pos in _parity_positions(updated):
            got = controller.span_at(char_pos)
            expected = _linear_span_at(updated, char_pos)
            assert got is expected, (
                f"post-toggle span_at({char_pos}) diverged from oracle "
                f"(got={got!r}, expected={expected!r})"
            )
    finally:
        _cleanup_controller(view, controller)


def test_span_at_high_n_queries_do_logarithmic_work_not_full_scans(
    qapp: QApplication,
) -> None:
    """AC-1 / AC-5: batch hover-style queries must examine O(log N) spans each.

    Instruments ``_spans`` so linear ``for`` scans and bisect probes both count.
    A full ``_spans`` scan would exceed the logarithmic budget; bisect must stay
    within it.
    """
    spans = _synthetic_spans(_SPAN_COUNT)
    view, controller = _make_controller(qapp, spans)
    try:
        instrumented = _InstrumentedSpans(controller.spans())
        controller._spans = instrumented  # type: ignore[assignment]

        queries: list[int] = []
        for span in spans[::8]:
            queries.append(span.start_pos)
            queries.append((span.start_pos + span.end_pos) // 2)
            queries.append(span.end_pos)
            queries.append(span.end_pos + 1)  # gap / miss between spans
        queries.append(-1)
        queries.append(spans[-1].end_pos + 100)

        # Confirm semantic answers while counting visits.
        for char_pos in queries:
            assert controller.span_at(char_pos) is _linear_span_at(spans, char_pos)

        query_count = len(queries)
        log_n = max(1, math.ceil(math.log2(_SPAN_COUNT)))
        # Generous probe budget for bisect_right + end check; far below N per query.
        budget = query_count * (8 * log_n + 4)
        visits = instrumented.item_visits
        assert visits <= budget, (
            f"span examinations={visits} exceed logarithmic "
            f"budget={budget} for {query_count} queries at N={_SPAN_COUNT} "
            f"(log2N={log_n}); linear _spans scan still in use"
        )
    finally:
        _cleanup_controller(view, controller)
