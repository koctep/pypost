# PYPOST-407: Technical Debt Analysis

## Review Summary

**Verdict:** SAFE TO CLOSE. Copy helper centralized, policy documented, `RequestData` lean
contract stated, tests added. Behavior unchanged; no blockers.

| Requirement | Status | Evidence |
| --- | --- | --- |
| Centralized copy helper | Met | `copy_request_for_isolated_tab` in `request_sync.py` |
| Copy policy documented | Met | Module docstring, `RequestData` docstring, `doc/dev/request_data_copy_policy.md` |
| RequestData stays lean | Met | Class docstring + `TestRequestDataLeanModel` |
| Tests for copy semantics | Met | `tests/test_request_sync.py` |
| No premature optimization | Met | Still uses `model_copy(deep=True)`; no shallow copy |

## Shortcuts Taken

- **Double copy retained** on Collections → `add_new_tab` path (defense-in-depth). Documented
  in copy policy; not optimized without profiling.
- **Save As** still uses inline `model_copy(deep=True, update={...})` — intentional exception
  for id/name override.

## Code Quality Issues

- `persisted_fields_equal` still compares full field values including large bodies (PYPOST-408
  note). Unchanged; hashing remains optional follow-up.

## Missing Tests

- No benchmark or memory test for very large request bodies. Acceptable — policy guards model
  shape; performance follow-up only if users report pain.

## Performance Concerns

- Deep copy cost still scales with `body`/`headers` size. Mitigated by keeping responses off
  `RequestData`. No change to runtime characteristics versus pre-task inline copies.

## Follow-up Tasks

| Priority | Description |
| --- | --- |
| Low | Optional: profile tab-open with multi-MB bodies if users store huge drafts | [PYPOST-608](https://pypost.atlassian.net/browse/PYPOST-608) |
| Low | Optional: field hashing in `persisted_fields_equal` if sibling sync becomes hot | [PYPOST-609](https://pypost.atlassian.net/browse/PYPOST-609) |

No new Jira tickets required to close PYPOST-407.
