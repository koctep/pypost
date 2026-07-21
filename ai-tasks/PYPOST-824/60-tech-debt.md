# PYPOST-824: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

## Shortcuts Taken

None material. Explicit post-close reselect via `navigable_tab_indices()` is the
hardening deferred from PYPOST-818 / PYPOST-820, implemented inline in `close_tab`
rather than extracted to a shared helper (acceptable for a ~10-line path).

## Code Quality Issues

- `close_tabs_for_request_ids` still calls `removeTab` in a loop without the same
  navigable reselect. Bulk delete of the rightmost open request tab(s) could leave
  current on `+`. Not required by this ticket’s acceptance tests; optional follow-up.
- Prefer extracting `_ensure_current_is_navigable(preferred_index)` if a third call site
  needs the same logic.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Close rightmost of three → not on `+` | Covered (fails before fix; passes after) |
| Close rightmost of two → not on `+` | Covered |
| `handle_close_tab` on rightmost → not on `+` | Covered |
| Close first / middle / last-only | Already covered (PYPOST-818/819/820) |
| Bulk `close_tabs_for_request_ids` focus after remove | Not covered; optional |

## Performance Concerns

None. Tab counts are small; one pass over navigable indices after close is negligible.

## Follow-up Tasks

| Item | Priority | Notes |
| ---- | -------- | ----- |
| Apply same navigable reselect after `close_tabs_for_request_ids` | Low | Same Qt `removeTab` trap if bulk-close removes tabs next to `+`. Jira: [PYPOST-831](https://pypost.atlassian.net/browse/PYPOST-831) |
| Close / retarget siblings PYPOST-825 and PYPOST-826 | Medium | Share root cause; no separate production change expected once this fix is merged |

## Blocker Review

**SAFE TO CLOSE** — acceptance criteria met; three named tests pass; related close-focus
coverage green; no production blockers. Siblings PYPOST-825 / PYPOST-826 are the same
defect class and should clear with this change.
