# PYPOST-319: Technical Debt Analysis

## Review Summary

**Verdict:** SAFE TO CLOSE. Save-as no longer triggers full tree rebuild and restore; incremental
insert path is tested and documented. Definition of Done met.

| Requirement | Status | Evidence |
| --- | --- | --- |
| Save-as avoids full tree rebuild | Met | `request_save_as_completed` → `add_saved_request_to_tree` |
| New collection support | Met | `_insert_collection_into_tree` when row missing |
| Expansion preserved | Met | `_expand_collection_if_saved` + StateManager update in tabs |
| Regular save unchanged | Met | Still uses `request_saved` → `refresh_tree` |
| Tests | Met | Presenter + tabs signal tests |

## Shortcuts Taken

- **Regular save still uses full `refresh_tree()`** — acceptable; only save-as was in scope.
- **No end-to-end GUI test** for save-as tree update — unit tests cover presenter and signal
  routing; broader save-as GUI tests tracked under PYPOST-320.

## Code Quality Issues

- None blocking. `add_saved_request_to_tree` mutates in-memory `col.requests` in tests only;
  production path relies on RequestManager already holding the new request.

## Missing Tests

- Integration test through real `MainWindow._wire_signals` without mocks (low value; wiring is
  one line).

## Performance Concerns

- Full tree rebuild on regular save remains O(n); defer unless profiling shows need.

## Follow-up Tasks

| Priority | Description |
| --- | --- |
| Low | Consider incremental tree update for regular save when only one request changes | [PYPOST-596](https://pypost.atlassian.net/browse/PYPOST-596) |
| Low | GUI save-as tests (PYPOST-320) | [PYPOST-597](https://pypost.atlassian.net/browse/PYPOST-597) |

No new Jira tickets required to close PYPOST-319.
