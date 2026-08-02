# PYPOST-979: Technical Debt Analysis

**Verdict: SAFE TO CLOSE.** No task-owned blocker or follow-up debt.

Test-only multi-tab characterizing proofs for session `wait_for_widget` /
`wait_for_enabled` with `in_current_tab=True` meet FR-1–FR-5 and AC-1–AC-6.
Closes [PYPOST-949](https://pypost.atlassian.net/browse/PYPOST-949) TD-2.
Production APIs, docs wording, logging, and metrics are unchanged.

## Review Scope

- `tests/test_ui_wait.py` (diff: two multi-tab proofs + `find_widget` import)
- `ai-tasks/PYPOST-979/` (requirements, architecture, cleanup, observability)
- Cross-check vs parent TD-2 in `ai-tasks/PYPOST-949/60-tech-debt.md`

No `pypost/` package changes in this task.

## Requirements and Architecture Review

| Item | Evidence | Verdict |
| --- | --- | --- |
| FR-1 / AC-1 | `test_session_wait_for_widget_in_current_tab_multi_tab` | Met |
| FR-2 / AC-2 | `test_session_wait_for_enabled_in_current_tab_multi_tab` | Met |
| FR-3 / AC-3 | Active rename → tab-scoped timeout; window still hits background; active disable → tab-scoped timeout | Met |
| FR-4 / AC-4 | Existing wait tests untouched in meaning; module `timeout(60)` + short isolation budgets | Met |
| FR-5 | `doc/dev/ui_wait.md` already documents optional current-tab scoping; no wording fix required in Step 4 | Met (Step 8 may note proofs) |
| AC-5 | No production / API / log / metric changes | Met |
| AC-6 | Explicit widget/enabled multi-tab proofs close PYPOST-949 TD-2 | Met |
| Architecture Test A/B | Identity + rename isolation; disable isolation + re-enable identity; local mutation only | Met |

No architecture deviations. Chosen plan (focused proofs in `test_ui_wait.py`,
no production or API change) was delivered as designed.

## Shortcuts Taken

None that leave incomplete DoD.

- Characterizing (expected-green) proofs instead of red-before-green production
  fix — intentional; tab-scoped routing already shipped in PYPOST-949.
- Enabled isolation does not also assert a window-scoped hit while active is
  disabled — matches architecture Test B (timeout alone proves AC-3 for
  enabled); widget proof already locks the window-vs-tab contrast.
- Developer doc update deferred to Step 8 only if a proof-citation is useful;
  current contract text is already accurate (FR-5).

## Code Quality Issues

None requiring follow-up.

- Shared multi-tab setup is duplicated with the text multi-tab sibling — same
  pattern as architecture; extracting a fixture would be optional polish, not
  debt for a 2-SP test-only close-out.
- `find_widget` import is used by both new proofs; cleanup report confirms no
  unused imports.
- Restore paths use `finally` for objectName and enabled state.

## Missing Tests

None for this ticket’s DoD.

| Scenario | Status |
| --- | --- |
| Tab-scoped `wait_for_widget` identity under active tab | Covered |
| Tab-scoped `wait_for_widget` isolation (active rename) | Covered |
| Window-scoped still finds background after active rename | Covered |
| Tab-scoped `wait_for_enabled` isolation (active disable) | Covered |
| Tab-scoped `wait_for_enabled` success identity after re-enable | Covered |
| Explicit pytest timeout markers | Present — module `pytestmark` includes `timeout(60)` |
| Multi-tab text wait | Out of scope (PYPOST-949) |
| Golden e2e / timeout-diagnostics | Out of scope (PYPOST-978 / PYPOST-950) |
| `wait_for_snapshot` tab-scoping | Out of scope |

Timeout-marker review: **no blocker**.

## Performance Concerns

None. Local widget mutation only (no HTTP stub). Isolation waits use
`timeout=0.5`; success paths use `timeout=5.0`; module bound at 60s. Step 5
scoped run: 2 passed in ~2s.

## Hardcoded Values

Test budgets (`0.5`, `5.0`) and role id `URL_INPUT` match architecture. Not
production policy; appropriate for characterizing proofs.

## Follow-up Tasks

None.

| Item | Priority | Description | Jira |
| --- | --- | --- | --- |
| — | — | No task-owned follow-up debt | — |

### Accepted / out of scope (do not ticket from this story)

- Wait redesign, new wait APIs, or default `in_current_tab=False` changes
- Expanding multi-tab text-wait coverage (PYPOST-949)
- Golden e2e text-wait migration ([PYPOST-978](https://pypost.atlassian.net/browse/PYPOST-978))
- Golden timeout-diagnostics lock ([PYPOST-950](https://pypost.atlassian.net/browse/PYPOST-950))
- Making `wait_for_snapshot` tab-scoped
- New `in_current_tab` log field / wait metrics (Step 6 correctly N/A)
- Step 8 developer-doc citation of the new proofs (workflow step, not debt)

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | None |
| Missing tests with timeout markers | **None** — markers present |
| Deviations from architecture | None |
| Acceptance gaps vs DoD | None — AC-1–AC-6 satisfied |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** for PYPOST-979 Step 7. Unticketed follow-ups: none.
