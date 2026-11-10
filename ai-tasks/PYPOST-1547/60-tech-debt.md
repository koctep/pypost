# PYPOST-1547: Technical Debt Analysis

## Shortcuts Taken

None. One toggle records a single length delta in `_SpanDeltaIndex` in
`pypost/ui/widgets/response_mask_controller.py`. Live `start_pos` and
`end_pos` are the formatted base plus the Fenwick prefix. `handle_click`
and `_apply_persisted_reveals` share `_replace_span_text`, which adds
that delta after `insertText`. Later spans are not visited and their
coordinates are not assigned. That is the plan in
`ai-tasks/PYPOST-1547/20-architecture.md`.

`update_visual_formats` still walks every span once to build
`ExtraSelection`s. Qt needs one selection per span. The walk reads live
positions and leaves the delta index unchanged. That paint pass is the
one `_spans` iteration the repro allows. It is the accepted design.

Pointer-motion throttling stays on
[PYPOST-1548](https://pypost.atlassian.net/browse/PYPOST-1548). This
ticket does not add a mouse-move throttle.

## Code Quality Issues

None. `_SpanDeltaIndex` is a 1-based Fenwick array with 0-based public
indexes. `prefix(0)` is 0. `add` on an empty index does nothing. An
index outside the array raises `IndexError`. `MaskedTokenSpan` keeps
constructor coordinates as the base so `start_pos` and `end_pos` can be
live properties. Equality and `repr` use those live positions and omit
the bind. No new hardcoded threshold was added. The gray and green
`ExtraSelection` colors in `update_visual_formats` are unchanged.

`spans()` still returns the controller's list. Callers that keep that
list see live coordinates through the properties. Production code does
not reorder the list after `set_masked_spans`. That return is
pre-existing.

The repro replaces `controller._spans` with an iterator counter after
bind. The span objects stay in the same order, so their Fenwick indexes
stay valid. A public test hook was not added. The same private-list
pattern is already accepted on PYPOST-1390.

## Missing Tests

None. `tests/test_pypost_1547_failing_repro.py` locks later click
targets after reveal of span 0, reveal of the middle span, and hide of
span 0, on 512 ordered spans. Each `handle_click` must store no
coordinates on any other span and must iterate `_spans` at most once.
Reveal shows the real value. Hide shows the mask. Paths and span count
stay the same. Gaps and positions outside every span miss.

The module declares an explicit timeout:

- `tests/test_pypost_1547_failing_repro.py` uses
  `pytestmark = pytest.mark.timeout(30)`.

Thirty seconds is the mark set for this document fixture in
`ai-tasks/PYPOST-1547/20-architecture.md`. The marker is the signal
default. The module does not set `method="thread"`. Every collected
test in that module is covered by the module marker.

The repro fixture has no reveal memory, which is what the architecture
asked for. Persisted reveal uses the same `_replace_span_text` add.
Correctness of restore stays on the existing PYPOST-1392 suite.
`clear_body` coverage, the async preserve regression, and pruning
`_reveal_state` stay on PYPOST-1549, PYPOST-1550, and PYPOST-1551.

## Performance Concerns

None as new work. Coordinate repair on a toggle is one Fenwick `add`,
O(log n), independent of how many spans follow.

`span_at` stays `bisect_right` on display start. Each probe reads one
prefix, so a search is O(log^2 n). The architecture accepts that cost
at the span counts this viewer uses. Mouse-move throttling, if
profiling still shows event-loop pressure, stays on
[PYPOST-1548](https://pypost.atlassian.net/browse/PYPOST-1548).

The paint pass is one walk. Each live coordinate is a prefix, so the
pass is O(n log n). The architecture leaves that pass in place. Clear
and `set_masked_spans` still unbind in one O(n) pass. That work is
outside the toggle budget.

## Follow-up Tasks

none

This change introduces no new follow-up. The Fenwick prefix of length
deltas is the work of this ticket. The paint walk that still visits
every span once is the accepted design. Mouse-move throttling stays on
PYPOST-1548 and is not re-filed. Reveal-memory tests and map pruning
stay on PYPOST-1549, PYPOST-1550, and PYPOST-1551. Menu and
editor-commit work stays on PYPOST-1557 and PYPOST-1558. Baseline and
flaky tests stay on PYPOST-1474, PYPOST-1475, PYPOST-1553,
PYPOST-1554, PYPOST-1555, and PYPOST-1556. This step records no
pre-existing test failure.

`doc/dev/hidden_response_fields.md` still describes a linear later-span
shift in `handle_click` and `_apply_persisted_reveals`. Bringing that
guide in line with the Fenwick prefix is Step 8.
