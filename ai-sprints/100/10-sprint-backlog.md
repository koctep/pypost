# Sprint 100 — Backlog

> Date: 2026-03-24
> Total issues: 3
> All issues: High priority · To Do

## Issues

| # | Key | Summary | Type | Priority | Status |
|---|-----|---------|------|----------|--------|
| 1 | PYPOST-400 | Stabilize post publishing API error handling | Debt | High | To Do |
| 2 | PYPOST-401 | Fix race condition in scheduling worker | Debt | High | To Do |
| 3 | PYPOST-402 | Add retry and alerting for email failures | Debt | High | To Do |

## Execution Order & Rationale

### 1 · PYPOST-400 — Stabilize post publishing API error handling
**Description:** Audit and stabilize API error handling for post publishing flow. Ensure consistent
status codes and actionable error messages.

**Rationale:** Foundational — consistent error contracts must exist before retry logic and alerting
can be built on top. Fixes observable surface-level failures first.

---

### 2 · PYPOST-401 — Fix race condition in scheduling worker
**Description:** Investigate and fix intermittent duplicate executions in the scheduling worker
caused by race conditions.

**Rationale:** Infrastructure stability. Duplicate job execution can corrupt state and interfere
with any retry mechanism introduced in PYPOST-402.

---

### 3 · PYPOST-402 — Add retry and alerting for email failures
**Description:** Implement retry strategy and operational alerts for failed outbound email
notifications in background jobs.

**Rationale:** Depends on a stable scheduler (PYPOST-401) and well-defined error codes
(PYPOST-400). Should be implemented last to avoid building on unstable foundations.

---

## Notes
- All issues are technical debt tagged `high-priority` and `sprint-mar24`.
- No blocked, done, or non-actionable issues — all three are ready for development execution.
