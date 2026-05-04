# Sprint 167 — Roadmap

> Date: 2026-03-26
> Methodology: Top-Down (Requirements → Architecture → Dev → Cleanup → Observability → Review →
> Docs → Commit)

## Sprint Steps

- [x] **STEP 1** — Sprint planning & backlog creation → `ai-sprints/167/10-sprint-backlog.md`
- [x] **STEP 2** — Junior Engineer sprint execution (agent-do.sh per issue) → `ai-sprints/167/40-sprint-execution.md`
- [x] **STEP 3** — Team Lead sprint report → `ai-sprints/167/90-sprint-report.md`

---

## Issue Progress

### Done (Sprint 167 — Final)

| # | Key | Summary | Type | Priority | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | PYPOST-420 | [PYPOST-402] Logger accumulation in AlertManager | Debt | Medium | Done |
| 2 | PYPOST-418 | [PYPOST-402] AlertManager never injected into RequestWorker | Debt | High | Done |
| 3 | PYPOST-419 | [PYPOST-402] AppSettings.default_retry_policy is persisted but never applied | Debt | High | Done |
| 4 | PYPOST-421 | [PYPOST-402] Bare assert in production retry path | Debt | Low | Done |
| 5 | PYPOST-422 | [PYPOST-402] email_notification_failures_total metric name is misleading | Debt | Low | Done |
| 6 | PYPOST-423 | [PYPOST-402] retryable_codes_edit silently drops invalid input | Debt | Low | Done |
| 7 | PYPOST-424 | [PYPOST-402] request_timeout spin box created but never added to form layout | Debt | Low | Done |
| 8 | PYPOST-437 | Add "Hidden" Checkbox for Variables | Feature | Medium | Done |

---

## Execution Checklist

### PYPOST-418 · AlertManager never injected into RequestWorker ✓ DONE

- [x] **Analyst** — gather requirements → `ai-tasks/PYPOST-418/10-requirements.md`
- [x] **Product Owner** — review requirements for business logic
- [x] **Senior Engineer** — create architecture → `ai-tasks/PYPOST-418/20-architecture.md`
- [x] **Team Lead** — review architecture
- [x] **Junior Engineer** — implement code (inner loop with Senior review)
- [x] **Junior Engineer** — code cleanup → `ai-tasks/PYPOST-418/40-code-cleanup.md`
- [x] **Senior Engineer** — observability → `ai-tasks/PYPOST-418/50-observability.md`
- [x] **Team Lead** — tech debt analysis → `ai-tasks/PYPOST-418/60-review.md`
- [x] **Team Lead** — dev docs → `ai-tasks/PYPOST-418/70-dev-docs.md`
- [x] **Team Lead** — final commit (`39eb591`)

### PYPOST-419 · AppSettings.default_retry_policy is persisted but never applied ✓ DONE

- [x] **Analyst** — gather requirements → `ai-tasks/PYPOST-419/10-requirements.md`
- [x] **Product Owner** — review requirements for business logic
- [x] **Senior Engineer** — create architecture → `ai-tasks/PYPOST-419/20-architecture.md`
- [x] **Team Lead** — review architecture
- [x] **Junior Engineer** — implement code (inner loop with Senior review)
- [x] **Junior Engineer** — code cleanup → `ai-tasks/PYPOST-419/40-code-cleanup.md`
- [x] **Senior Engineer** — observability → `ai-tasks/PYPOST-419/50-observability.md`
- [x] **Team Lead** — tech debt analysis → `ai-tasks/PYPOST-419/60-review.md`
- [x] **Team Lead** — dev docs → `ai-tasks/PYPOST-419/70-dev-docs.md`
- [x] **Team Lead** — final commit (`24a7656`)

### PYPOST-420 · Logger accumulation in AlertManager ✓ DONE

- [x] **Analyst** — gather requirements → `ai-tasks/PYPOST-420/10-requirements.md`
- [x] **Product Owner** — review requirements for business logic
- [x] **Senior Engineer** — create architecture → `ai-tasks/PYPOST-420/20-architecture.md`
- [x] **Team Lead** — review architecture
- [x] **Junior Engineer** — implement code (inner loop with Senior review)
- [x] **Junior Engineer** — code cleanup → `ai-tasks/PYPOST-420/40-code-cleanup.md`
- [x] **Senior Engineer** — observability → `ai-tasks/PYPOST-420/50-observability.md`
- [x] **Team Lead** — tech debt analysis → `ai-tasks/PYPOST-420/60-review.md`
- [x] **Team Lead** — dev docs → `ai-tasks/PYPOST-420/70-dev-docs.md`
- [x] **Team Lead** — final commit (a397a18)

---

### PYPOST-421 · Bare assert in production retry path

- [x] **Analyst** — gather requirements → `ai-tasks/PYPOST-421/10-requirements.md`
- [x] **Product Owner** — review requirements for business logic
- [x] **Senior Engineer** — create architecture → `ai-tasks/PYPOST-421/20-architecture.md`
- [x] **Team Lead** — review architecture
- [x] **Junior Engineer** — implement code (inner loop with Senior review)
- [x] **Junior Engineer** — code cleanup → `ai-tasks/PYPOST-421/40-code-cleanup.md`
- [x] **Senior Engineer** — observability → `ai-tasks/PYPOST-421/50-observability.md`
- [x] **Team Lead** — tech debt analysis → `ai-tasks/PYPOST-421/60-review.md`
- [x] **Team Lead** — dev docs → `ai-tasks/PYPOST-421/70-dev-docs.md`
- [x] **Team Lead** — final commit (`231a24c`)

### PYPOST-422 · email_notification_failures_total metric name is misleading

- [x] **Analyst** — gather requirements → `ai-tasks/PYPOST-422/10-requirements.md`
- [x] **Product Owner** — review requirements for business logic
- [x] **Senior Engineer** — create architecture → `ai-tasks/PYPOST-422/20-architecture.md`
- [x] **Team Lead** — review architecture
- [x] **Junior Engineer** — implement code (inner loop with Senior review)
- [x] **Junior Engineer** — code cleanup → `ai-tasks/PYPOST-422/40-code-cleanup.md`
- [x] **Senior Engineer** — observability → `ai-tasks/PYPOST-422/50-observability.md`
- [x] **Team Lead** — tech debt analysis → `ai-tasks/PYPOST-422/60-review.md`
- [x] **Team Lead** — dev docs → `ai-tasks/PYPOST-422/70-dev-docs.md`
- [x] **Team Lead** — final commit (`0c19432`)

### PYPOST-423 · retryable_codes_edit silently drops invalid input

- [x] **Analyst** — gather requirements → `ai-tasks/PYPOST-423/10-requirements.md`
- [x] **Product Owner** — review requirements for business logic
- [x] **Senior Engineer** — create architecture → `ai-tasks/PYPOST-423/20-architecture.md`
- [x] **Team Lead** — review architecture
- [x] **Junior Engineer** — implement code (inner loop with Senior review)
- [x] **Junior Engineer** — code cleanup → `ai-tasks/PYPOST-423/40-code-cleanup.md`
- [x] **Senior Engineer** — observability → `ai-tasks/PYPOST-423/50-observability.md`
- [x] **Team Lead** — tech debt analysis → `ai-tasks/PYPOST-423/60-review.md`
- [x] **Team Lead** — dev docs → `ai-tasks/PYPOST-423/70-dev-docs.md`
- [x] **Team Lead** — final commit (`b897782`)

### PYPOST-424 · request_timeout spin box created but never added to form layout

- [x] **Analyst** — gather requirements → `ai-tasks/PYPOST-424/10-requirements.md`
- [x] **Product Owner** — review requirements for business logic
- [x] **Senior Engineer** — create architecture → `ai-tasks/PYPOST-424/20-architecture.md`
- [x] **Team Lead** — review architecture
- [x] **Junior Engineer** — implement code (inner loop with Senior review)
- [x] **Junior Engineer** — code cleanup → `ai-tasks/PYPOST-424/40-code-cleanup.md`
- [x] **Senior Engineer** — observability → `ai-tasks/PYPOST-424/50-observability.md`
- [x] **Team Lead** — tech debt analysis → `ai-tasks/PYPOST-424/60-review.md`
- [x] **Team Lead** — dev docs → `ai-tasks/PYPOST-424/70-dev-docs.md`
- [x] **Team Lead** — final commit (`d644190`)

---

### PYPOST-437 · Commit lint.sh, test.sh, and .gitignore updates

- [x] **Analyst** — gather requirements → `ai-tasks/PYPOST-437/10-requirements.md`
- [x] **Product Owner** — review requirements for business logic
- [x] **Senior Engineer** — create architecture → `ai-tasks/PYPOST-437/20-architecture.md`
- [x] **Team Lead** — review architecture (approved 2026-03-27)
- [x] **Junior Engineer** — implement code (inner loop with Senior review)
- [x] **Junior Engineer** — code cleanup → `ai-tasks/PYPOST-437/40-code-cleanup.md`
- [x] **Senior Engineer** — observability → `ai-tasks/PYPOST-437/50-observability.md`
- [x] **Team Lead** — tech debt analysis → `ai-tasks/PYPOST-437/60-tech-debt.md`
- [x] **Team Lead** — dev docs → `ai-tasks/PYPOST-437/70-dev-docs.md`
- [x] **Team Lead** — final commit (`6015984`)

---

## Project Manager Update

**Date**: 2026-05-04
**Phase**: `sprint_complete` — all 8 issues closed.

### Status

Sprint 167 has **8 issues**: 8 **Done**, 0 **In Progress**.

| # | Key | Summary | Priority | Status | Commit |
| --- | --- | --- | --- | --- | --- |
| 1 | PYPOST-420 | Logger accumulation in AlertManager | Medium | **Done** | `a397a18` |
| 2 | PYPOST-418 | AlertManager never injected into RequestWorker | High | **Done** | `39eb591` |
| 3 | PYPOST-419 | default_retry_policy persisted but never applied | High | **Done** | `24a7656` |
| 4 | PYPOST-421 | Bare assert in production retry path | Low | **Done** | `231a24c` |
| 5 | PYPOST-422 | email_notification_failures_total metric name is misleading | Low | **Done** | `0c19432` |
| 6 | PYPOST-423 | retryable_codes_edit silently drops invalid input | Low | **Done** | `b897782` |
| 7 | PYPOST-424 | request_timeout spin box created but never added to form layout | Low | **Done** | `d644190` |
| 8 | PYPOST-437 | Add "Hidden" Checkbox for Variables | Medium | **Done** | `6015984` |

### Completed Milestones

- PYPOST-420: all deliverables complete, final commit `a397a18` — 17/17 tests pass.
- PYPOST-418: all deliverables complete, final commit `39eb591` — 274/274 tests pass.
- PYPOST-419: all deliverables complete, final commit `24a7656` — 26/26 tests pass.
- PYPOST-421: all deliverables complete, final commit `231a24c` — 49/49 tests pass.
- PYPOST-422: all deliverables complete, final commit `0c19432` — 42/42 tests pass.
- PYPOST-423: all deliverables complete, final commit `b897782` — 49/49 tests pass.
- PYPOST-424: all deliverables complete, final commit `d644190` — 292/292 tests pass.
- PYPOST-437: all deliverables complete, final commit `6015984` — 83/83 tests pass.
- Sprint execution report: `ai-sprints/167/40-sprint-execution.md` created.
- Sprint final report: `ai-sprints/167/90-sprint-report.md` updated to include PYPOST-437.

### Active Risks / Blockers

None. Sprint 167 is fully closed.

### Next Action

Sprint 167 complete. Follow-up debt items from PYPOST-437 tracked in PYPOST-446, PYPOST-447,
PYPOST-448, PYPOST-449.
