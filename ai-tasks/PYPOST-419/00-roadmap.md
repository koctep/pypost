# PYPOST-419 — AppSettings.default_retry_policy Persisted But Never Applied

> Sprint: 167
> Date: 2026-03-26
> Type: Tech Debt (child of PYPOST-402)
> Priority: High
> Methodology: Top-Down (Requirements → Architecture → Dev → Cleanup → Observability →
> Review → Docs → Commit)

## Summary

`AppSettings.default_retry_policy` is serialised to and deserialised from disk, but
`RequestWorker` never reads it at runtime. The retry feature is therefore inert end-to-end.
This was flagged as RISK-2 carry-forward in Sprint 134.

---

## Deliverables Checklist

- [x] **10-requirements.md** — Analyst gathers requirements
- [x] **20-architecture.md** — Senior Engineer creates architecture
- [x] **40-code-cleanup.md** — Junior Engineer performs code cleanup
- [x] **50-observability.md** — Senior Engineer implements observability
- [x] **60-review.md** — Team Lead tech-debt analysis
- [x] **70-dev-docs.md** — Team Lead dev docs
- [x] **Final commit** — Team Lead commits
- [ ] **Jira closure** — Project Manager closes issue

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
| 8 | Project Manager | Jira closure | **Pending** |

---

## Context

- **Root cause**: `AppSettings.default_retry_policy` is loaded from disk on startup but is
  never passed to or read by `RequestWorker`, leaving the retry feature silently inert.
- **Impact**: Users who configure a retry policy (via `AppSettings`) see no effect; all
  requests run without retry regardless of the setting.
- **Dependency**: PYPOST-420 (logger fix) and PYPOST-418 (AlertManager injection) must land
  first — both are now **done** (commits `a397a18` and `39eb591`).
- **Execution order in Sprint 167**: PYPOST-420 (done) → PYPOST-418 (done) →
  **PYPOST-419** (this issue, now unblocked).

---

## Project Manager Update

**Date**: 2026-03-26
**Phase**: `observability_ready` — observability pass complete; ready for Team Lead
review, dev docs, and final commit.

### Completed Milestones

- PYPOST-420 fully closed (commit `a397a18` — AlertManager logger accumulation fixed).
- PYPOST-418 fully closed (commit `39eb591` — AlertManager wired into RequestWorker via
  full DI chain).
- Sprint 167 execution order established; PYPOST-419 is the last remaining issue.
- **`10-requirements.md` delivered** — FR-1 through FR-5, AC-1 through AC-5, policy
  resolution precedence confirmed: per-request > AppSettings default > hardcoded fallback.
- **Product Owner review complete** — requirements approved.
- **`20-architecture.md` delivered** — Senior Engineer chose to inject `Optional[RetryPolicy]`
  (not full `AppSettings`) into `RequestService`; single two-line insert in
  `_execute_http_with_retry`; `RequestWorker` forwards the resolved value; `tabs_presenter`
  reads from `self._settings.default_retry_policy` at construction time. Three-file scope:
  `request_service.py`, `worker.py`, `tabs_presenter.py`.
- **Team Lead architecture review complete** — approved.
- **Implementation complete** — Junior Engineer delivered all three production file changes
  (`request_service.py`, `worker.py`, `tabs_presenter.py`) and new test class
  `TestRequestServiceRetryPolicyResolution` (3 branch tests: AC-1, AC-2, AC-3).
- **`40-code-cleanup.md` delivered** — all 26 tests pass; no cleanup issues found; zero dead
  code, unused imports, or line-length violations.
- **`50-observability.md` delivered** — Senior Engineer added 3 targeted debug-log lines:
  injection log in `RequestService.__init__`, policy resolution source log in
  `_execute_http_with_retry` (per_request / app_default / hardcoded_fallback), and
  forwarding log in `RequestWorker.__init__`. Full DI chain is now traceable end-to-end.
  No new metrics or alerting changes required; existing `track_retry_attempt` and
  `_emit_exhaustion_alert` calls remain sufficient.

### Active Risks / Blockers

- No blockers.
- No remaining risks — all implementation, compatibility, and observability concerns resolved.

### Next Action

- **team_lead** → `60-review.md` tech-debt analysis, `70-dev-docs.md`, and final commit.
- **project_manager** → Jira closure once commit lands.
