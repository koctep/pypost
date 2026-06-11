# PYPOST-406: Technical Debt Analysis

## Review Summary

**Verdict:** SAFE TO CLOSE. Left-click and `add_new_tab` now deep-copy `RequestData`, matching
**New tab** and session-restore isolation. Definition of Done is met; tests cover emit-site
and tab-layer isolation. Residual debt is optional polish, not blockers.

| Requirement | Status | Evidence |
| --- | --- | --- |
| Left-click opens tab with independent working copy | Met | `_on_collection_clicked` emits `model_copy(deep=True)` |
| Dual tabs do not share mutable state | Met | `add_new_tab` deep-copies; presenter + tabs tests |
| Save/rename/stale flows unchanged | Met | Same `request_id` on copies; no wiring changes |
| Folder click still expand/collapse only | Met | Unchanged branch in `_on_collection_clicked` |
| Automated isolation tests | Met | `test_open_request_in_tab_emits_deep_copy_on_click`, `test_add_new_tab_deep_copies_request_data` |

## Shortcuts Taken

- **Defense-in-depth double copy:** context-menu and left-click paths may copy twice (presenter
  emit + `add_new_tab`). Acceptable per architecture; negligible for typical request sizes.
- **Dual signals retained:** `open_request_in_tab` and `open_request_in_isolated_tab` both route
  to `add_new_tab`; merging signals was explicitly out of scope.

## Code Quality Issues

- Signal docstrings note deep-copy semantics but do not document that `add_new_tab` is the
  canonical enforcement point — covered in dev docs (Step 7).
- Left-click does not increment `gui_new_tab_actions_total` while context menu does; log-only
  tracking for left-click unless metrics follow-up is added.

## Missing Tests

- No end-to-end test through `MainWindow` wiring (signal → `add_new_tab` → editor mutation).
  Presenter-level tests are sufficient for the scoped change.
- No explicit test that history-load path receives a copy via `add_new_tab` (acceptable
  side effect documented in architecture).

## Performance Concerns

- Double `model_copy(deep=True)` on context-menu path for large bodies/headers. Same trade-off
  as PYPOST-405 restore path; acceptable for typical requests.

## Follow-up Tasks

| Priority | Description |
| --- | --- |
| Low | Optional: `track_gui_new_tab_action("collections_click")` on left-click for metric parity |
| Low | Optional: merge `open_request_in_tab` / `open_request_in_isolated_tab` if product wants one signal |
| Low | Optional: integration test via `MainWindow` for full open path |

No new Jira tickets required to close PYPOST-406.
