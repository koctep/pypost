"""Failing repro for PYPOST-1547.

One reveal or hide must keep every later click target on the value now
shown. Coordinate repair must not write later spans or walk ``_spans``
again to apply the length delta. The paint pass is the one allowed walk.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass

import pytest
from PySide6.QtWidgets import QApplication

from pypost.ui.widgets.foldable_code_view import FoldableCodeView
from pypost.ui.widgets.response_mask_controller import (
    MaskedTokenSpan,
    ResponseMaskController,
)

pytestmark = pytest.mark.timeout(30)

_SPAN_COUNT = 512
_PREFIX = "lead"
_MASK = "***"
_GAP = ".."
_TAIL = "tail"
_COORDINATES = ("start_pos", "end_pos")


@dataclass
class _ClickBudget:
    """Counts later-span coordinate writes and ``_spans`` iteration calls."""

    other_writes: int = 0
    iter_calls: int = 0
    toggled_id: int | None = None

    def reset(self, toggled: MaskedTokenSpan) -> None:
        self.other_writes = 0
        self.iter_calls = 0
        self.toggled_id = id(toggled)


_BUDGET = _ClickBudget()


class _ObservedSpan(MaskedTokenSpan):
    """Counts ``start_pos`` / ``end_pos`` stores on spans other than the toggle."""

    def __setattr__(self, name: str, value: object) -> None:
        if name in _COORDINATES:
            toggled_id = _BUDGET.toggled_id
            if toggled_id is not None and toggled_id != id(self):
                _BUDGET.other_writes += 1
        object.__setattr__(self, name, value)


class _IterCountedSpans(list[MaskedTokenSpan]):
    """Counts ``__iter__`` calls without counting bisect ``__getitem__`` probes."""

    def __iter__(self) -> Iterator[MaskedTokenSpan]:
        _BUDGET.iter_calls += 1
        return list.__iter__(self)


@dataclass(frozen=True)
class _ToggleSample:
    label: str
    other_writes: int
    iter_calls: int


def _build_ordered_spans(count: int) -> tuple[str, list[MaskedTokenSpan]]:
    """Ordered non-overlapping spans with a prefix and a gap after each token."""
    parts = [_PREFIX]
    spans: list[MaskedTokenSpan] = []
    cursor = len(_PREFIX)
    for index in range(count):
        start = cursor
        end = start + len(_MASK)
        spans.append(
            _ObservedSpan(
                start_pos=start,
                end_pos=end,
                raw_value=f"value-{index:04d}",
                masked_value=_MASK,
                path=f"field.{index}",
            )
        )
        parts.append(_MASK)
        parts.append(_GAP)
        cursor = end + len(_GAP)
    parts.append(_TAIL)
    return "".join(parts), spans


def _assert_fixture(document_text: str, spans: Sequence[MaskedTokenSpan]) -> None:
    """Lock the layout the click assertions measure against."""
    assert len(_PREFIX) >= 1
    assert len(_GAP) >= 2
    assert len(spans) == _SPAN_COUNT
    assert len({span.path for span in spans}) == len(spans)
    assert document_text.startswith(_PREFIX)
    assert spans[0].start_pos == len(_PREFIX)
    for index, span in enumerate(spans):
        assert span.end_pos == span.start_pos + len(span.masked_value)
        assert len(span.raw_value) > len(span.masked_value)
        assert span.is_revealed is False
        assert document_text[span.start_pos:span.end_pos] == span.masked_value
        if index + 1 < len(spans):
            assert spans[index + 1].start_pos - span.end_pos >= 2
        else:
            assert span.end_pos < len(document_text)


def _make_controller(
    document_text: str,
    spans: list[MaskedTokenSpan],
) -> tuple[FoldableCodeView, ResponseMaskController]:
    view = FoldableCodeView()
    view.setPlainText(document_text)
    controller = ResponseMaskController(view)
    controller.set_masked_spans(spans)
    controller._spans = _IterCountedSpans(controller._spans)
    return view, controller


def _cleanup(view: FoldableCodeView, controller: ResponseMaskController) -> None:
    """Detach the viewport filter before closing to avoid teardown eventFilter noise."""
    viewport = view.viewport()
    if viewport is not None:
        viewport.removeEventFilter(controller)
    controller.clear()
    view.close()


def _capture(spans: Sequence[MaskedTokenSpan]) -> list[tuple[int, int]]:
    return [(span.start_pos, span.end_pos) for span in spans]


def _set_revealed(
    deltas: list[int],
    spans: Sequence[MaskedTokenSpan],
    index: int,
    revealed: bool,
) -> None:
    span = spans[index]
    if revealed:
        deltas[index] = len(span.raw_value) - len(span.masked_value)
    else:
        deltas[index] = 0


def _toggle(
    controller: ResponseMaskController,
    span: MaskedTokenSpan,
    label: str,
) -> _ToggleSample:
    char_pos = span.start_pos
    _BUDGET.reset(span)
    handled = controller.handle_click(char_pos)
    sample = _ToggleSample(label, _BUDGET.other_writes, _BUDGET.iter_calls)
    assert handled is True, f"{label}: handle_click missed the span"
    return sample


def _assert_neighbors(
    controller: ResponseMaskController,
    spans: Sequence[MaskedTokenSpan],
    captured: Sequence[tuple[int, int]],
    index: int,
) -> None:
    """Spans before the toggle keep their positions; later spans move."""
    toggled_start, toggled_end = captured[index]
    assert spans[index].start_pos == toggled_start
    assert spans[index].end_pos != toggled_end
    for cursor, span in enumerate(spans):
        old_start, old_end = captured[cursor]
        if cursor < index:
            assert span.start_pos == old_start
            assert span.end_pos == old_end
            mid = (old_start + old_end) // 2
            assert controller.span_at(old_start) is span
            assert controller.span_at(mid) is span
            assert controller.span_at(old_end) is span
        elif cursor > index:
            assert span.start_pos != old_start
            assert span.end_pos != old_end


def _assert_state(
    view: FoldableCodeView,
    controller: ResponseMaskController,
    spans: Sequence[MaskedTokenSpan],
    bases: Sequence[tuple[int, int]],
    deltas: Sequence[int],
    paths: Sequence[str],
) -> None:
    """Live positions are base plus prefix deltas; hits, gaps, and text follow."""
    assert len(spans) == _SPAN_COUNT
    assert [span.path for span in spans] == list(paths)
    text = view.toPlainText()
    carried = 0
    for index, span in enumerate(spans):
        base_start, base_end = bases[index]
        start = base_start + carried
        carried += deltas[index]
        end = base_end + carried
        assert span.start_pos == start, f"span {index} start {span.start_pos} != {start}"
        assert span.end_pos == end, f"span {index} end {span.end_pos} != {end}"
        revealed = deltas[index] != 0
        assert span.is_revealed == revealed
        shown = span.raw_value if revealed else span.masked_value
        assert text[start:end] == shown, f"span {index} slice is not the shown value"
        mid = (start + end) // 2
        assert controller.span_at(start) is span, f"span {index} missed its live start"
        assert controller.span_at(mid) is span, f"span {index} missed its midpoint"
        assert controller.span_at(end) is span, f"span {index} missed its inclusive end"
        gap_pos = end + 1
        if index + 1 < len(spans):
            next_start = bases[index + 1][0] + carried
            assert gap_pos < next_start
        assert controller.span_at(gap_pos) is None, f"span {index} gap {gap_pos} hit"
    assert spans[0].start_pos > 0
    assert controller.span_at(0) is None
    assert controller.span_at(spans[0].start_pos - 1) is None
    assert controller.span_at(spans[-1].end_pos + 1) is None


def _assert_outside_clicks(
    controller: ResponseMaskController,
    spans: Sequence[MaskedTokenSpan],
) -> None:
    prefix_pos = spans[0].start_pos - 1
    past_end = spans[-1].end_pos + 1
    assert controller.span_at(prefix_pos) is None
    assert controller.handle_click(prefix_pos) is False
    assert controller.span_at(past_end) is None
    assert controller.handle_click(past_end) is False


def test_handle_click_keeps_later_targets_without_linear_span_walk(
    qapp: QApplication,
) -> None:
    """Reveal span 0, reveal a middle span, then hide span 0.

    Later spans stay the hit at their live start, midpoint, and inclusive
    end. Gaps and positions outside every span miss. Reveal shows the real
    value and hide shows the mask. Each ``handle_click`` may iterate
    ``_spans`` once for paint and must not store coordinates on any other span.
    """
    assert qapp is not None
    document_text, spans = _build_ordered_spans(_SPAN_COUNT)
    bases = [(span.start_pos, span.end_pos) for span in spans]
    paths = [span.path for span in spans]
    _assert_fixture(document_text, spans)
    view, controller = _make_controller(document_text, spans)
    try:
        assert view.toPlainText() == document_text
        assert isinstance(controller._spans, _IterCountedSpans)
        deltas = [0] * _SPAN_COUNT
        measured: list[_ToggleSample] = []

        captured = _capture(spans)
        _set_revealed(deltas, spans, 0, True)
        measured.append(_toggle(controller, spans[0], "reveal span 0"))
        _assert_neighbors(controller, spans, captured, 0)
        _assert_state(view, controller, spans, bases, deltas, paths)
        _assert_outside_clicks(controller, spans)

        middle = _SPAN_COUNT // 2
        captured = _capture(spans)
        _set_revealed(deltas, spans, middle, True)
        measured.append(_toggle(controller, spans[middle], "reveal middle span"))
        _assert_neighbors(controller, spans, captured, middle)
        _assert_state(view, controller, spans, bases, deltas, paths)

        captured = _capture(spans)
        _set_revealed(deltas, spans, 0, False)
        measured.append(_toggle(controller, spans[0], "hide span 0"))
        _assert_neighbors(controller, spans, captured, 0)
        _assert_state(view, controller, spans, bases, deltas, paths)

        for sample in measured:
            assert sample.other_writes == 0 and sample.iter_calls <= 1, (
                f"{sample.label}: linear later-span writes={sample.other_writes} "
                f"(want 0); _spans.__iter__ calls={sample.iter_calls} "
                "(want at most 1, the paint pass)"
            )
    finally:
        _cleanup(view, controller)
