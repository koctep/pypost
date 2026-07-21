# PYPOST-887: Technical Debt Analysis

## Shortcuts Taken

None. The fix is a small, intentional lifecycle helper (`_discard_chunk_buffer`)
called from finish, error, and send — matching the architecture in
`20-architecture.md`. No temporary workarounds or feature flags.

## Code Quality Issues

Little / no debt. Mixin helper + three call sites is clear; docstring documents
the race. Optional future polish (not required now):

- Chunk buffer / timer maps remain keyed by `id(tab)` (pre-existing pattern);
  same as other tab-scoped dicts on `TabsPresenter`.

## Missing Tests

None for the reported race. `tests/test_tabs_presenter_response_display.py`
covers:

- Stream-then-finish (pending flush discarded; body once)
- Same race for GET (not PUT-only)
- Error path discard
- Send path discard before a new request

Timeouts: module-level `pytestmark = pytest.mark.timeout(60)`.

## Performance Concerns

None. Discard is O(1) dict pops + timer `stop` / `deleteLater`. Flush interval
remains 33 ms (`_chunk_flush_ms`).

## User documentation (`doc/user/`)

N/A. Internal race between streamed `append_body` and final `display_response`;
no user-facing behavior change beyond “body shown once.” No user doc update.

## Follow-up Tasks

None. No follow-up Jira issues required for this fix.
