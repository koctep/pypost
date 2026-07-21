# PYPOST-831: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE — bulk-close reselect matches single-close rule;
helper extracted; focused presenter tests green; no new unticketed debt.

## Shortcuts Taken

None material. Implementation follows `20-architecture.md`:

- PYPOST-824 reselect body extracted to `_ensure_current_is_navigable`
- `close_tab` calls the helper (behavior-preserving)
- `close_tabs_for_request_ids` calls it once after the reverse `removeTab`
  loop with `preferred = max(0, min(indices_to_close) - 1)`
- Empty-request-tab path still uses `add_new_tab` only (no helper)

No temporary workarounds or duplicated reselect blocks remain.

## Code Quality Issues

None introduced. Production change is a small private helper plus two call
sites; comments only explain the Qt `removeTab` / trailing-`+` focus trap.

Pre-existing polish (not blocking; do not re-file):

| Item | Severity | Notes |
| --- | --- | --- |
| `close_tabs_for_request_ids(request_ids: list)` lacks element type | Low | Pre-existing signature; out of scope for this focus fix |

## Missing Tests

| Scenario | Status |
| --- | --- |
| Bulk-close rightmost request tab → not on `+` | Covered |
| Bulk-close multiple rightmost → not on `+` | Covered |
| Bulk-close all request tabs → blank replacement, not `+` | Covered (strengthened assert) |
| Single-close rightmost / middle / last-only | Covered (PYPOST-818/819/820/824) |
| Module `pytestmark = pytest.mark.timeout(60)` | Present — **no timeout blocker** |
| MainWindow e2e / GUI automation for bulk focus | Not covered — **out of scope** (accepted in requirements) |

Optional gaps that are **accepted / not follow-ups**:

- No dedicated unit test of `_ensure_current_is_navigable` in isolation
  (covered via `close_tab` and `close_tabs_for_request_ids` paths).
- No extra assert for non-contiguous bulk sets; product rule is final focus
  not on `+`, which the rightmost cases lock in.

## Performance Concerns

None. One `navigable_tab_indices()` pass after bulk remove; tab counts stay
small.

## Resolved Debt

| Source | Item | Resolution |
| --- | --- | --- |
| PYPOST-824 TD | Apply navigable reselect after `close_tabs_for_request_ids` | Done in this ticket |
| PYPOST-824 note | Extract `_ensure_current_is_navigable` when a second call site appears | Done (single- + bulk-close) |

## Follow-up Tasks

No new unticketed follow-up debt from PYPOST-831.

| Priority | Item | Rationale |
| -------- | ---- | --------- |
| — | None | Acceptance met; architecture followed; no remedial work required |

Phase D should not create Debt tickets from this file unless new items are
added later.

## Blocker Review

**SAFE TO CLOSE** — Definition of Done met; focused suite
(`close_tabs_for_request_ids` / `land_on_plus` / `close_tab`) **12 passed**;
timeout markers present; no production blockers; user-doc update not
applicable (focus consistency fix, not a documented workflow change).
