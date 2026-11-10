# PYPOST-1544: Technical Debt Analysis

## Shortcuts Taken

None. `MaskBreadcrumb` keeps a wildcard count and updates it on push and
pop. A hierarchical miss reads `has_wildcard`. Redaction and the response
viewer pass that breadcrumb. Mask results stay the same. That is the plan
in `ai-tasks/PYPOST-1544/20-architecture.md`.

One-shot lists and tuples still scan their own segments in
`_sequence_has_wildcard`. A plain sequence has no push or pop history, so
that check keeps today's yes or no. Production walks do not take that
branch. This is the accepted design, not a new ticket.

`sensitive_text_sanitizer._redact_node` copies an incoming plain path onto
a breadcrumb by `push` before the recursive redact. `redact_json_response_fields`
still calls `redact_tree`. The copy is not a new ticket.

## Code Quality Issues

None. `MaskBreadcrumb` subclasses `list`. `append` forwards to `push` so a
leftover append cannot leave the count behind. `extend` and `insert` are
not overridden. Walks call `push` and `pop`. That limit is the architecture.
It is not a new ticket.

`CompiledPathSelector.raw` is still assigned and unread. The attribute was
already unread before this ticket. It is not filed again.

## Missing Tests

None. `tests/test_pypost_1544_failing_repro.py` locks the miss path, the
redact and formatter `push` sites, and the live mask decisions. Those
decisions include a shorthand hit, a shorthand miss, an outer star after
an inner list pop, and an object key that is `"*"`.

The module declares an explicit timeout:

- `tests/test_pypost_1544_failing_repro.py` uses
  `pytestmark = pytest.mark.timeout(30)`.

Thirty seconds is the pure-unit band. Every collected test in that module
is covered by the module marker.

## Performance Concerns

None as new work. A hierarchical miss on a `MaskBreadcrumb` reads
`has_wildcard` from the count. It does not scan the location again.

One-shot lists and tuples still scan their own segments. That remaining
scan is the accepted design for a sequence that was never pushed, and it
is not a new ticket. The second shorthand trie walk stays gated on
presence. An isolated trie catalog and wildcard fan-out stay on
PYPOST-1545.

## Follow-up Tasks

none

This change introduces no new follow-up. Knowing wildcard presence from
push and pop is the work of this ticket. One-shot lists still scan their
own segments; that is the accepted design, not a new ticket. The isolated
trie catalog stays on PYPOST-1545. Other sprint work stays on PYPOST-1547,
PYPOST-1548, PYPOST-1549, PYPOST-1550, PYPOST-1551, PYPOST-1557, and
PYPOST-1558. Baseline and flaky tests stay on PYPOST-1474, PYPOST-1475,
PYPOST-1553, PYPOST-1554, PYPOST-1555, and PYPOST-1556. This step records
no pre-existing test failure.

The selector-engine guide already describes `has_wildcard` on the
breadcrumb and the one-shot segment check. User docs do not describe the
miss-path scan. That note is for Step 8. It is not a follow-up ticket.
