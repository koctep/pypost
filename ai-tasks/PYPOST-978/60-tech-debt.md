# PYPOST-978: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE. Closes PYPOST-949 TD-1 (optional golden migration to
tab-scoped session `wait_for_text`). No task-owned blocker debt and **no new
follow-up Jira items**. Step 8 still owns developer-doc accuracy updates.

Scope reviewed: `tests/test_agent_golden_e2e.py`,
`tests/test_agent_e2e_response_panel.py` (convention marker), and
`ai-tasks/PYPOST-978/*`. Production `pypost/` wait code unchanged.

## Shortcuts Taken

- **Docs deferred to Step 8** — Architecture and FR-5 planned accuracy edits in
  `doc/dev/ui_wait.md` and `doc/dev/agent_golden_e2e.md`. Not a Step 7 ticket;
  owned by STEP 8 of this task.
- **Success settle left on shared helper** — Intentional. PYPOST-970 already
  routes success through `wait_response_after_send(..., in_current_tab=True)`.
  Re-inlining would undo DRY.
- **Timeout companion stays inline** — Intentional PYPOST-950 design: force a
  status miss and assert diagnostics. Folding into the success helper would
  obscure that purpose (architecture rejected that option).
- **Full `make check` / full `make test-agent-e2e` not re-run in Steps 5–6** —
  Scoped golden + convention proofs green; acceptable for this 1-SP test-only
  call-site change. Not residual product debt.
- **Free `find_widget` import retained** — Out of scope. Only free-function
  **text-wait** imports were in scope for removal.

## Code Quality Issues

None blocking.

- Companion call site matches architecture:
  `session.wait_for_text(RESPONSE_STATUS, "Status: 999", timeout=0.05,
  in_current_tab=True)`.
- Free `wait_for_text` import and unused `tab` binding removed.
- AST convention helpers live next to sibling golden DRY locks in
  `test_agent_e2e_response_panel.py` — consistent with PYPOST-970; no extract
  needed for a single marker.
- Companion fill/click remain window-scoped (pre-existing); only the wait entry
  point was migrated. Single-tab fixture; settle semantics unchanged. Not a
  crutch introduced by this ticket.

## Missing Tests

| Scenario | Status |
| -------- | ------ |
| No free `wait_for_text` import in golden | Covered (AST marker) |
| Golden `wait_for_text` is `session.wait_for_text` only | Covered |
| Each call passes `in_current_tab=True` | Covered |
| Golden success Send → settle | Covered (existing + shared helper) |
| Plus-tab / no-blank-tab flow | Covered (existing) |
| Forced-timeout diagnostics (`step`, excerpt, …) | Covered (PYPOST-950 companion) |
| Explicit pytest timeout markers | Present — module `timeout(10)` / `timeout(60)` |
| Tab-scoped `wait_for_widget` / `wait_for_enabled` | Out of scope — PYPOST-979 |
| Free-function wait unit proofs | Intentionally remain in `tests/test_ui_wait.py` |

Timeout-marker review: **no blocker** — both touched modules declare
`pytestmark` with `pytest.mark.timeout(...)`.

## Performance Concerns

None. Same short 50 ms forced miss and same shared success settle budgets;
tab-scoped root may slightly narrow findChild walks. AST marker is
milliseconds, no GUI.

## Deviations from Architecture

None material. Delivered selected option: migrate companion only; keep success
on shared helper; add AST free-import / session-call marker; docs in Step 8.

## Follow-up Tasks

Concrete Debt candidates for later sync. **None for this story.**

| ID | Priority | Item | Notes | Jira |
| -- | -------- | ---- | ----- | ---- |
| — | — | No task-owned follow-up debt | PYPOST-949 TD-1 closed by this ticket | n/a |

### Already ticketed elsewhere (do not re-ticket)

| Item | Owner |
| ---- | ----- |
| Tab-scoped `wait_for_widget` / `wait_for_enabled` proofs | [PYPOST-979](https://pypost.atlassian.net/browse/PYPOST-979) |
| Golden timeout-diagnostics companion contract | [PYPOST-950](https://pypost.atlassian.net/browse/PYPOST-950) (done; companion style only changed here) |

### Accepted / out of scope (do not ticket from this story)

- Step 8 developer doc accuracy (`ui_wait.md` still says free-function “golden
  e2e pattern”; `agent_golden_e2e.md` companion wording still says bare
  `wait_for_text` without `session.` / `in_current_tab=True`) — STEP 8.
- Changing default session wait scope (`in_current_tab=False`).
- Removing free-function waits from production or from unit tests that target
  them.
- Expanding the AST marker beyond `tests/test_agent_golden_e2e.py`.
- Aligning companion fill/click to `in_current_tab=True` (cosmetic; optional
  hygiene, not required for AC).
- New production logs/metrics (Step 6 correctly N/A).

## Blocker Review

| Check | Result |
| ----- | ------ |
| Temporary solutions / crutches | None that block ship |
| Missing tests with timeout markers | **None** — markers present |
| Deviations from architecture | None |
| Acceptance gaps vs DoD | **None** — AC-1–AC-6 satisfied in code; FR-5 docs = Step 8 |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** for PYPOST-978 Step 7. No Phase D Jira creates from this
file. Proceed to STEP 8 for doc accuracy.
