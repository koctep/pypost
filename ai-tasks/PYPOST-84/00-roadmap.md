# PYPOST-84 Roadmap — ScriptExecutor patch targets class not instance

## Overview

**Type**: Tech Debt (MEDIUM)
**Source**: ai-tasks/PYPOST-52/60-review.md
**Labels**: PYPOST-52, tech-debt
**Priority**: Medium

### Problem Statement

In `tests/test_request_service.py` (class `TestRequestServicePostScript` and
`TestRequestServiceErrorHandling`), `ScriptExecutor` is patched at the class level:

```python
with patch("pypost.core.request_service.ScriptExecutor") as mock_executor:
    mock_executor.execute.return_value = ({"x": 1}, ["log"], None)
```

The concern raised in PYPOST-52's review: if `RequestService` ever instantiates
`ScriptExecutor` before calling `execute`, the correct mock target would be
`mock_executor.return_value.execute.return_value`, not `mock_executor.execute`.

**Current finding**: `ScriptExecutor.execute` is a `@staticmethod` in production code
(`pypost/core/script_executor.py:49`). `RequestService` calls it as
`ScriptExecutor.execute(...)` (class-level), not `ScriptExecutor().execute(...)`.
Therefore the current mocking approach is technically correct — but the tests lack
a comment making this contract explicit, which is the source of confusion and risk.

### Scope of Fix

1. Verify `@staticmethod` decoration is intentional and stable.
2. Add an inline comment in each `patch("...ScriptExecutor")` block clarifying that
   `mock_executor.execute` is used because `execute` is a `@staticmethod`.
3. Alternatively, if the team decides `ScriptExecutor` should become instance-based,
   update both production code and tests accordingly.

---

## Deliverables

| # | Artifact | Owner | Status |
|---|----------|-------|--------|
| 1 | `10-requirements.md` | analyst | ✅ done |
| 2 | `20-architecture.md` | senior_engineer | ✅ done |
| 3 | Code fix in `tests/test_request_service.py` | junior_engineer | ✅ done |
| 4 | `40-code-cleanup.md` | junior_engineer | ✅ done |
| 5 | `50-observability.md` | senior_engineer | ✅ done |
| 6 | `60-review.md` | team_lead | ✅ done |
| 7 | `70-dev-docs.md` | team_lead | ✅ done |

---

## Milestones

| Phase | Status | Notes |
|-------|--------|-------|
| Kickoff / Roadmap | ✅ Done | 2026-03-25 |
| Requirements | ✅ Done | 2026-03-25 |
| Architecture | ✅ Done | 2026-03-25 |
| Implementation | ✅ Done | 2026-03-25 |
| Code Cleanup | ✅ Done | 2026-03-25 |
| Observability | ✅ Done | 2026-03-25 |
| Review + Docs | ✅ Done | 2026-03-25 |
| Final commit | ✅ Done | 2026-03-25 |

---

## Project Manager Update — 2026-03-25 (architecture_ready)

### Completed Milestones
- Kickoff: roadmap created, Jira issue reviewed, production code inspected.
- Root cause confirmed: `ScriptExecutor.execute` is a `@staticmethod`; current mocking
  is functionally correct but undocumented. Affected test locations:
  - `TestRequestServicePostScript` lines 63–64, 71–72
  - `TestRequestServiceErrorHandling` lines 216–217, 236–237
- **Requirements complete** (`10-requirements.md`): fix scope decided as comment-only
  clarification at four patch sites in `tests/test_request_service.py`. No production
  code changes required. AC-1–AC-4 defined.
- **Architecture complete** (`20-architecture.md`): exact three-line comment wording
  defined for all four patch sites; verification plan (`make test`) documented; AC
  mapping confirmed. No production code changes required.

### Active Risks / Blockers
- **Risk**: If `ScriptExecutor.execute` is ever changed from `@staticmethod` to an
  instance method (likely during PYPOST-43–51 refactoring), all four mock sites will
  silently break. This is the primary motivation for the fix.
- No blockers at this time.

### Next Action
- **junior_engineer**: Implement the comment-only fix in `tests/test_request_service.py`
  at the four sites (lines 64, 72, 217, 237) using the exact wording from
  `20-architecture.md`, then run `make test` to confirm 0 failures. Produce
  `40-code-cleanup.md` upon completion.

---

## Project Manager Update — 2026-03-25 (implementation_ready)

### Completed Milestones
- Kickoff, requirements, architecture: all complete (see prior PM update above).
- **Implementation complete**: comment-only fix applied at all four patch sites in
  `tests/test_request_service.py` (lines 64, 72, 217, 237) per `20-architecture.md`.
- **Code cleanup complete** (`40-code-cleanup.md`): no executable code changed; all
  style checks pass; `make test` reports **195 passed, 0 failures, 0 errors**.
- AC-1–AC-4 all satisfied.

### Active Risks / Blockers
- **Residual risk**: if `ScriptExecutor.execute` is promoted to an instance method
  during PYPOST-43–51 refactoring, all four mock sites will now surface the mismatch
  via the added comments — the primary goal of this fix is achieved.
- No blockers at this time.

### Next Action
- **senior_engineer**: Produce `50-observability.md` (assess whether any logging,
  metrics, or alerting hooks are relevant for this comment-only change — expected to
  be brief/N/A given no executable code was modified).
- After observability: **team_lead** to produce `60-review.md` + `70-dev-docs.md`
  and perform the final commit.

---

## Project Manager Update — 2026-03-25 (observability_ready)

### Completed Milestones
- Kickoff, requirements, architecture: complete (see prior PM updates above).
- **Implementation complete**: comment-only fix at all four `mock_executor.execute.return_value`
  sites in `tests/test_request_service.py`.
- **Code cleanup complete** (`40-code-cleanup.md`): 195 passed, 0 failures, style clean.
- **Observability complete** (`50-observability.md`): assessed as N/A — no executable code
  changed, no logging/metrics/alerting additions required. Future consideration documented:
  if `execute` is ever promoted to an instance method, a DEBUG log and metrics review should
  accompany that refactor.
- All ACs (AC-1–AC-4) remain satisfied.

### Active Risks / Blockers
- **Residual risk (unchanged)**: silent mock breakage if `ScriptExecutor.execute` is promoted
  to an instance method during PYPOST-43–51 refactoring. Mitigated by the four comments now
  in place.
- No blockers at this time.

### Next Action
- **team_lead**: Produce `60-review.md` (tech-debt analysis) and `70-dev-docs.md` (developer
  documentation), then perform the final commit for PYPOST-84.

---

## Project Manager Update — 2026-03-25 (finalization)

### Completed Milestones
- All seven deliverables verified complete:
  - `10-requirements.md` ✅ — fix scoped to comment-only additions, AC-1–AC-4 defined.
  - `20-architecture.md` ✅ — exact 3-line comment wording specified for all four patch sites.
  - Code fix ✅ — comments applied at lines 64, 72, 217, 237 of `tests/test_request_service.py`.
  - `40-code-cleanup.md` ✅ — 195 passed, 0 failures, style clean; no executable code changed.
  - `50-observability.md` ✅ — assessed N/A; future consideration for instance-method refactor documented.
  - `60-review.md` ✅ — all AC criteria PASS; residual TD-1 (MEDIUM, pre-existing) documented; no new debt introduced.
  - `70-dev-docs.md` ✅ — developer guide covering mock contract rationale and migration steps written.
- Final commit completed: 2026-03-25.
- All ACs satisfied:
  - AC-1 ✅ All four `mock_executor.execute.return_value` lines annotated.
  - AC-2 ✅ Comments state the required change if `execute` becomes an instance method.
  - AC-3 ✅ `make test` — 195 passed, 0 failures, 0 errors.
  - AC-4 ✅ Only `tests/test_request_service.py` was modified.

### Active Risks / Blockers
- No blockers. No active risks.
- Residual forward-looking risk (TD-1, MEDIUM): silent mock breakage if `ScriptExecutor.execute`
  is promoted to an instance method during PYPOST-43–51 refactoring. Fully mitigated by the
  four in-place comments; ownership passed to that task scope.

### Next Action
- **None.** All deliverables complete. PYPOST-84 is closed.
