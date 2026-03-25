# PYPOST-403 Roadmap — [HP] Fix failing tests in CI

**Type**: Debt
**Priority**: Highest
**Labels**: high-priority, tech-debt, tests
**Status**: Done

## Summary

Investigate and fix currently failing automated tests in CI. Ensure test suite is stable
and green for the default pipeline.

---

## Milestones

| # | Phase                  | Deliverable               | Status      |
|---|------------------------|---------------------------|-------------|
| 0 | Kickoff                | Roadmap initialized       | ✅ Done     |
| 1 | Requirements           | 10-requirements.md        | ✅ Done     |
| 2 | Product Owner Review   | Requirements approved     | ✅ Done     |
| 3 | Architecture           | 20-architecture.md        | ✅ Done     |
| 4 | Team Lead Review       | Architecture approved     | ✅ Done     |
| 5 | Implementation         | Code changes + cleanup    | ✅ Done     |
| 6 | Observability          | 50-observability.md       | ✅ Done     |
| 7 | Review & Docs          | 60-review.md, 70-dev-docs | ✅ Done     |
| 8 | Commit & Close         | Final commit + Jira close | ✅ Done     |

---

## Project Manager Update

**Date**: 2026-03-25
**Phase**: finalization confirmed — All 8 phases verified complete.

### Completed Milestones
- Phase 0 — Roadmap initialized; Jira PYPOST-403 transitioned to In Progress.
- Phase 1 — Requirements complete (`10-requirements.md`): 5 failing tests across 2 root causes
  (SSE probe `AttributeError` × 3, HistoryManager race `OSError` × 2).
- Phase 2 — Product Owner review complete; requirements approved.
- Phase 3 — Architecture complete (`20-architecture.md`): surgical fixes designed for all 5
  failures plus crash-dump housekeeping. 6 files in scope.
- Phase 4 — Team Lead review complete; architecture approved.
- Phase 5 — Implementation and code cleanup complete (`40-code-cleanup.md`):
  - `pypost/core/http_client.py`: default-construct `TemplateService()` when arg is `None`.
  - `pypost/core/history_manager.py`: store `_save_thread`; add `flush()` method.
  - `tests/test_http_client_sse_probe.py`: inject `TemplateService` in `setUp`; use `self.client`.
  - `tests/test_history_manager.py`: `hm.flush()` before temp dir cleanup in 2 tests.
  - `tests/test_http_client.py`: updated test name to reflect new default-construct contract.
  - `.gitignore`: added `core` / `core.*` ELF dump patterns; `core` crash dump deleted.
  - **Result**: `191 passed` — test suite fully green.
- Phase 6 — Observability complete (`50-observability.md`):
  - `history_manager.py`: cap-enforcement WARNING log; save timing with `elapsed_ms`; `flush()`
    lifecycle DEBUG logs.
  - `http_client.py`: default `TemplateService` construction DEBUG log; SSE detection DEBUG log;
    successful response DEBUG log (`request_complete method/status/elapsed_ms/size`).
  - 24 affected tests continue to pass; log lines are non-breaking (DEBUG/WARNING only).
- Phase 7 — Review & Docs complete (`60-review.md`, `70-dev-docs.md`): no new debt; two
  minor low-severity items noted for backlog (crash root cause investigation, SSE heuristic
  improvement); all code quality dimensions rated Good/Excellent.
- Phase 8 — Final commit applied (`afd2a58`); all deliverables shipped.

### Active Risks / Blockers
- None. All 5 failures resolved, all acceptance criteria met, 191 tests green, commit applied.

### Next Action
- Finalization complete. Jira PYPOST-403 transitioned to Done.
- Backlog items to consider: (1) investigate root cause of deleted `core` crash dump;
  (2) replace SSE URL heuristic with content-type-based detection (low priority).
