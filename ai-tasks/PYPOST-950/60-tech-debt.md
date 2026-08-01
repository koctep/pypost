# PYPOST-950: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Golden forced-timeout companion now uses tab-scoped `wait_for_text` miss on
`RESPONSE_STATUS` with impossible label `Status: 999`, preserving
`step=wait_response_after_send` and `response_excerpt` wrapping. Text-wait
inner diagnostics (`widget_id`, `expected`) are asserted. TD-3 from PYPOST-920
is closed. No production changes; golden module green.

## Shortcuts Taken

- **Companion test inlines wrap pattern** instead of calling
  `wait_response_after_send`. Matches pre-existing golden style; helper already
  covers siblings (PYPOST-948).
- **Only status wait forced in timeout test.** Body text-wait miss not
  duplicated — status mismatch is sufficient to prove text-wait timeout path
  with shorter test runtime.
- **Full `make check` not re-run.** Step 5 validated lint + scoped golden
  module (3 passed).

## Code Quality Issues

None blocking. Test mirrors `_golden_fill_send_and_settle` tab root and wrap
shape; doc updated in Step 8.

Architecture vs implementation:

| Architecture | Implementation | Assessment |
| --- | --- | --- |
| Tab-scoped `wait_for_text` miss | `wait_for_text(tab, RESPONSE_STATUS, "Status: 999", …)` | Match |
| Keep step + response_excerpt wrap | Unchanged pattern | Match |
| Assert text-wait diagnostics | `widget_id`, `expected` | Match |
| No production changes | Test + docs only | Match |

## Missing Tests

| Scenario | Status |
| --- | --- |
| Forced golden timeout on text-wait path | Covered |
| step + response_excerpt on wrap | Covered |
| Inner text-wait diagnostics preserved | Covered |
| Body-first forced text-wait miss | Not covered — unnecessary duplicate |
| Sibling timeout companions on text-wait | Separate tickets (PYPOST-934, etc.) |

**No timeout-marker blockers.**

## Performance Concerns

None. Text-wait miss with 50ms budget is faster than snapshot predicate poll.

## Follow-up Tasks

| ID | Priority | Task | Notes | Jira |
| -- | -------- | ---- | ----- | ---- |
| — | — | None from this ticket | TD-3 closed | — |

### Unticketed follow-ups (for orchestrator)

None required from PYPOST-950. Parent epic follow-ups remain elsewhere:

1. **Sibling e2e panel-walk → text-wait** — PYPOST-948 scope (Medium).
2. **Tab-scoped session text waits** — PYPOST-949 (Low).
3. **Other agent e2e timeout companions** — mapping (PYPOST-955), dialog
   (PYPOST-934) — align with text-wait when those modules migrate settle.

## User documentation

N/A — no `doc/user/` changes.

## Blocker Review

**SAFE TO CLOSE** — acceptance met: timeout diagnostics test uses
`wait_for_text` miss while keeping `step` + `response_excerpt` wrapping;
golden module passes; dev docs updated.

## Worklog

```
tokens_used: 42000
role: execution
step: 7
step_name: Review
```
