# PYPOST-1548: Technical Debt Analysis

## Shortcuts Taken

None. Hover feedback for a masked response coalesces only when the
caller passes `limit_hover_moves=True`. The default is false.
`ResponseView` still builds `ResponseMaskController(self.body_view, self)`,
so today's move still applies the cursor and tooltip inside the event
filter. With the limit on, one single-shot `QTimer` at interval 0
applies the newest local point and global point once through
`_apply_hover_feedback` and `span_at`. A click still uses the release
position. That is the plan in
`ai-tasks/PYPOST-1548/20-architecture.md`.

## Code Quality Issues

None. The timer, the waiting flag, and the two stored points are
created only when the flag is true. `_cancel_limited_hover` returns
immediately when the flag is false, so the default path never touches
those fields. Leave, `clear`, and `clear_spans` clear the waiting flag,
stop the timer, and drop the stored points. `handle_click` still calls
`span_at` on the release character. The interval is 0. Tooltip wording
stays `"Click to reveal"` and `"Click to re-mask"`.

The repro still catches `TypeError` and assigns `_limit_hover_moves`
when the constructor rejects the keyword. With the keyword present,
construction takes the green path and that branch is unused. Assigning
the flag alone does not create the timer. The delivered call is
`ResponseMaskController(view, limit_hover_moves=True)`.

## Missing Tests

None. `tests/test_pypost_1548_failing_repro.py` locks the enabled
limit: three synchronous viewport moves apply hover feedback zero
times until one `processEvents`, then once, for the latest global
point, with `PointingHandCursor`. `handle_click` at that character
toggles that span and leaves the earlier span masked.

The module declares an explicit timeout:

- `tests/test_pypost_1548_failing_repro.py` uses
  `pytestmark = pytest.mark.timeout(30)`.

Thirty seconds is the mark set for this widget fixture in
`ai-tasks/PYPOST-1548/20-architecture.md`. The marker is the signal
default. The module does not set `method="thread"`. Every collected
test in that module is covered by the module marker. The flush is one
`processEvents` drain. The module has no `threading.Event` and no
`QTest.qWait`.

`_apply_hover_feedback` is the shared cursor and tooltip body, and the
repro runs it for a span hit. The default flag applies that helper
inside the move event. Leave, `clear`, and `clear_spans` drop a pending
pass. The architecture named this one repro and left unused-limit click
results on the existing click suites. `clear_body` coverage, the async
preserve regression, and pruning `_reveal_state` stay on PYPOST-1549,
PYPOST-1550, and PYPOST-1551.

## Performance Concerns

None as new work. With the flag off, each `MouseMove` still does one
`span_at` plus cursor and tooltip work, which is the path
`ResponseView` uses. With the flag on, a burst keeps the newest point
and runs that work once on the next event-loop turn. The timer interval
is 0. There is no sleep and no millisecond cap.

`span_at` stays `bisect_right` plus one Fenwick prefix, as delivered by
PYPOST-1390 and PYPOST-1547. The paint walk in `update_visual_formats`
is unchanged.

## Follow-up Tasks

none

This change introduces no new follow-up. The optional trailing coalesce
is the work of this ticket. Keeping it off in `ResponseView` is the
accepted default. Reveal-memory tests and map pruning stay on
PYPOST-1549, PYPOST-1550, and PYPOST-1551. Menu and editor-commit work
stays on PYPOST-1557 and PYPOST-1558. Baseline and flaky tests stay on
PYPOST-1474, PYPOST-1475, PYPOST-1553, PYPOST-1554, PYPOST-1555, and
PYPOST-1556. This step records no pre-existing test failure. No Jira
issue was created.

`doc/dev/hidden_response_fields.md` still describes immediate
`MouseMove` cursor and tooltip updates and points optional throttling
at this ticket. `doc/user/requests.md` still matches the default hover
wording. Bringing the developer guide in line with the optional
coalesce is Step 8.
