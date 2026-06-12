# PYPOST-47: Technical Debt Analysis

## Review Summary

**Verdict:** SAFE TO CLOSE. Collection reads are unified through RequestManager; UI refresh
paths no longer bypass the manager or redundantly reload disk after in-memory CRUD. Definition
of Done met.

| Requirement | Status | Evidence |
| --- | --- | --- |
| No UI direct storage reads for collections | Met | Tree uses `get_collections()` only |
| Disk reload via RequestManager only | Met | `load_collections()` delegates to `reload_collections()` |
| Post-save refresh without redundant disk I/O | Met | `request_saved` → `refresh_tree` |
| Startup without double reload | Met | `refresh_tree` after RequestManager init |
| Tests | Met | Presenter + MainWindow tests added |

## Shortcuts Taken

- **`load_collections()` kept as combined reload+refresh** for backward compatibility and tests
  that simulate storage changes between calls.
- **External JSON edits** while the app runs still require explicit `load_collections()` if a
  future “Refresh collections” action is added; not implemented in this task.

## Code Quality Issues

- None blocking. `FakeRequestManager` in tests still exposes `.storage` for reload simulation;
  could align with `tests.helpers.FakeStorageManager` in a future cleanup (PYPOST-85 pattern).

## Missing Tests

- No integration test exercising save → `refresh_tree` end-to-end through real RequestManager +
  presenter (unit-level coverage deemed sufficient for this refactor).

## Performance Concerns

- Eliminated one redundant `storage.load_collections()` on every startup and every tab save.

## Follow-up Tasks

| Priority | Description |
| --- | --- |
| Low | Optional: user-facing “Reload collections from disk” menu action calling `load_collections()` | [PYPOST-629](https://pypost.atlassian.net/browse/PYPOST-629) |
| Low | Optional: unify `FakeRequestManager` with `tests.helpers.FakeStorageManager` | [PYPOST-630](https://pypost.atlassian.net/browse/PYPOST-630) |

No new Jira tickets required to close PYPOST-47.
