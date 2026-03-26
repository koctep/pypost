# PYPOST-418 — AlertManager Never Injected into RequestWorker

> Sprint: 167
> Date: 2026-03-26
> Type: Tech Debt (child of PYPOST-402)
> Priority: High
> Methodology: Top-Down (Requirements → Architecture → Dev → Cleanup → Observability →
> Review → Docs → Commit)

## Summary

`AlertManager` is instantiated during application bootstrap but is never passed to
`RequestWorker`. As a result, all alert callbacks (request-failure notifications, timeout
alerts) are dead code in production. This was flagged as RISK-1 carry-forward in Sprint 134.

---

## Deliverables Checklist

- [x] **10-requirements.md** — Analyst gathers requirements
- [x] **20-architecture.md** — Senior Engineer creates architecture
- [x] **40-code-cleanup.md** — Junior Engineer performs code cleanup
- [x] **50-observability.md** — Senior Engineer implements observability
- [x] **60-review.md** — Team Lead tech-debt analysis
- [x] **70-dev-docs.md** — Team Lead dev docs
- [x] **Final commit** — Team Lead commits
- [x] **Jira closure** — Project Manager closes issue

---

## Step Progress

| Step | Role | Deliverable | Status |
|------|------|-------------|--------|
| 1 | Analyst | `10-requirements.md` | **Done** |
| 2 | Product Owner | Requirements review | **Done** |
| 3 | Senior Engineer | `20-architecture.md` | **Done** |
| 4 | Team Lead | Architecture review | **Done** |
| 5 | Junior Engineer | Implementation (inner loop) | **Done** |
| 5b | Junior Engineer | `40-code-cleanup.md` | **Done** |
| 6 | Senior Engineer | `50-observability.md` | **Done** |
| 7 | Team Lead | `60-review.md` | **Done** |
| 7b | Team Lead | `70-dev-docs.md` | **Done** |
| 7c | Team Lead | Final commit | **Done** |
| 8 | Project Manager | Jira closure | **Done** |

---

## Context

- **Root cause**: `AlertManager` instance created in bootstrap/entrypoint is not forwarded
  to `RequestWorker.__init__`, leaving all alert hooks disconnected.
- **Impact**: Alert callbacks for request failures and timeouts never fire in production;
  the feature is silently inert.
- **Dependency**: Requires PYPOST-420 to have landed first (clean `AlertManager` logger).
  PYPOST-420 is **done** (commit `a397a18`).
- **Execution order in Sprint 167**: PYPOST-420 (done) → **PYPOST-418** (this issue) →
  PYPOST-419.

---

## Project Manager Update

**Date**: 2026-03-26
**Phase**: `closed` — All deliverables complete; Jira issue closed.

### Completed Milestones

- PYPOST-420 fully closed (commit `a397a18`; `AlertManager` logger clean).
- Sprint 167 execution order established; PYPOST-418 unblocked.
- `10-requirements.md` complete — 7 FRs, 3 NFRs, 7 ACs, key files and risks documented.
- Product Owner requirements review — approved.
- `20-architecture.md` complete — full DI chain `main.py → MainWindow → TabsPresenter →
  RequestWorker → RequestService`; config extension, bootstrap, test plan (4 new tests),
  and AC traceability all covered.
- Team Lead architecture review — approved.
- Implementation complete — all 5 source files modified, 4 new injection tests added.
- `40-code-cleanup.md` complete — 274 tests passing (274 passed, 0 failed); imports
  ordered, no dead code, 100-char line limit respected.
- `50-observability.md` complete — 4 structured log lines added across the full DI chain
  (`main.py` INFO, `main_window.py` DEBUG, `tabs_presenter.py` DEBUG, `worker.py` DEBUG);
  operators can confirm injection state and bisect failures from the log stream alone.
- `60-review.md` complete — all 7 ACs pass; 3 low-severity non-blocking observations
  (TD-1/TD-2/TD-3); verdict: APPROVED.
- `70-dev-docs.md` complete — DI chain diagram, config table, changed-file annotations,
  observable log stream, and test documentation.
- Final commit landed: `39eb591` — AlertManager wired into RequestWorker via DI chain.
- Jira PYPOST-418 transitioned to Done.

### Active Risks / Blockers

- None. Issue fully closed.
- Carry-forward debt items pre-registered: PYPOST-433 (`close()` at exit).
- PYPOST-419 (retry policy) is now unblocked.

### Next Action

- **project_manager** → close Sprint 167 PYPOST-418 work; unblock PYPOST-419.
