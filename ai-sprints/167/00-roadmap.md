# Sprint 167 — Roadmap

> Date: 2026-03-26
> Methodology: Top-Down (Requirements → Architecture → Dev → Cleanup → Observability → Review →
> Docs → Commit)

## Sprint Steps

- [x] **STEP 1** — Sprint planning & backlog creation → `ai-sprints/167/10-sprint-backlog.md`
- [x] **STEP 2** — Junior Engineer sprint execution (agent-do.sh per issue) → `ai-sprints/167/40-sprint-execution.md`
- [ ] **STEP 3** — Team Lead sprint report → `ai-sprints/167/90-sprint-report.md`

---

## Issue Progress

### Done (Sprint 167 — Wave 1)

| # | Key | Summary | Type | Priority | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | PYPOST-420 | [PYPOST-402] Logger accumulation in AlertManager | Debt | Medium | Done |
| 2 | PYPOST-418 | [PYPOST-402] AlertManager never injected into RequestWorker | Debt | High | Done |
| 3 | PYPOST-419 | [PYPOST-402] AppSettings.default_retry_policy is persisted but never applied | Debt | High | Done |

---

### Open (Sprint 167 — Remaining Scope)

| # | Key | Summary | Type | Priority | Status |
| --- | --- | --- | --- | --- | --- |
| 4 | PYPOST-421 | [PYPOST-402] Bare assert in production retry path | Debt | Low | To Do |
| 5 | PYPOST-422 | [PYPOST-402] email_notification_failures_total metric name is misleading | Debt | Low | To Do |
| 6 | PYPOST-423 | [PYPOST-402] retryable_codes_edit silently drops invalid input | Debt | Low | To Do |
| 7 | PYPOST-424 | [PYPOST-402] request_timeout spin box created but never added to form layout | Debt | Low | To Do |

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

- [ ] **Analyst** — gather requirements → `ai-tasks/PYPOST-421/10-requirements.md`
- [ ] **Product Owner** — review requirements for business logic
- [ ] **Senior Engineer** — create architecture → `ai-tasks/PYPOST-421/20-architecture.md`
- [ ] **Team Lead** — review architecture
- [ ] **Junior Engineer** — implement code (inner loop with Senior review)
- [ ] **Junior Engineer** — code cleanup → `ai-tasks/PYPOST-421/40-code-cleanup.md`
- [ ] **Senior Engineer** — observability → `ai-tasks/PYPOST-421/50-observability.md`
- [ ] **Team Lead** — tech debt analysis → `ai-tasks/PYPOST-421/60-review.md`
- [ ] **Team Lead** — dev docs → `ai-tasks/PYPOST-421/70-dev-docs.md`
- [ ] **Team Lead** — final commit

### PYPOST-422 · email_notification_failures_total metric name is misleading

- [ ] **Analyst** — gather requirements → `ai-tasks/PYPOST-422/10-requirements.md`
- [ ] **Product Owner** — review requirements for business logic
- [ ] **Senior Engineer** — create architecture → `ai-tasks/PYPOST-422/20-architecture.md`
- [ ] **Team Lead** — review architecture
- [ ] **Junior Engineer** — implement code (inner loop with Senior review)
- [ ] **Junior Engineer** — code cleanup → `ai-tasks/PYPOST-422/40-code-cleanup.md`
- [ ] **Senior Engineer** — observability → `ai-tasks/PYPOST-422/50-observability.md`
- [ ] **Team Lead** — tech debt analysis → `ai-tasks/PYPOST-422/60-review.md`
- [ ] **Team Lead** — dev docs → `ai-tasks/PYPOST-422/70-dev-docs.md`
- [ ] **Team Lead** — final commit

### PYPOST-423 · retryable_codes_edit silently drops invalid input

- [ ] **Analyst** — gather requirements → `ai-tasks/PYPOST-423/10-requirements.md`
- [ ] **Product Owner** — review requirements for business logic
- [ ] **Senior Engineer** — create architecture → `ai-tasks/PYPOST-423/20-architecture.md`
- [ ] **Team Lead** — review architecture
- [ ] **Junior Engineer** — implement code (inner loop with Senior review)
- [ ] **Junior Engineer** — code cleanup → `ai-tasks/PYPOST-423/40-code-cleanup.md`
- [ ] **Senior Engineer** — observability → `ai-tasks/PYPOST-423/50-observability.md`
- [ ] **Team Lead** — tech debt analysis → `ai-tasks/PYPOST-423/60-review.md`
- [ ] **Team Lead** — dev docs → `ai-tasks/PYPOST-423/70-dev-docs.md`
- [ ] **Team Lead** — final commit

### PYPOST-424 · request_timeout spin box created but never added to form layout

- [ ] **Analyst** — gather requirements → `ai-tasks/PYPOST-424/10-requirements.md`
- [ ] **Product Owner** — review requirements for business logic
- [ ] **Senior Engineer** — create architecture → `ai-tasks/PYPOST-424/20-architecture.md`
- [ ] **Team Lead** — review architecture
- [ ] **Junior Engineer** — implement code (inner loop with Senior review)
- [ ] **Junior Engineer** — code cleanup → `ai-tasks/PYPOST-424/40-code-cleanup.md`
- [ ] **Senior Engineer** — observability → `ai-tasks/PYPOST-424/50-observability.md`
- [ ] **Team Lead** — tech debt analysis → `ai-tasks/PYPOST-424/60-review.md`
- [ ] **Team Lead** — dev docs → `ai-tasks/PYPOST-424/70-dev-docs.md`
- [ ] **Team Lead** — final commit

---

## Project Manager Update

**Date**: 2026-03-27
**Phase**: `execution_partial` — wave 1 complete; sprint scope still active.

### Status

Sprint 167 has **7 issues**: 3 **Done**, 4 **To Do**.

| # | Key | Summary | Priority | Status | Commit |
| --- | --- | --- | --- | --- | --- |
| 1 | PYPOST-420 | Logger accumulation in AlertManager | Medium | **Done** | `a397a18` |
| 2 | PYPOST-418 | AlertManager never injected into RequestWorker | High | **Done** | `39eb591` |
| 3 | PYPOST-419 | default_retry_policy persisted but never applied | High | **Done** | `24a7656` |
| 4 | PYPOST-421 | Bare assert in production retry path | Low | **To Do** | — |
| 5 | PYPOST-422 | email_notification_failures_total metric name is misleading | Low | **To Do** | — |
| 6 | PYPOST-423 | retryable_codes_edit silently drops invalid input | Low | **To Do** | — |
| 7 | PYPOST-424 | request_timeout spin box created but never added to form layout | Low | **To Do** | — |

### Completed Milestones

- PYPOST-420: all deliverables complete, final commit `a397a18` — 17/17 tests pass.
- PYPOST-418: all deliverables complete, final commit `39eb591` — 274/274 tests pass.
- PYPOST-419: all deliverables complete, final commit `24a7656` — 26/26 tests pass.
- Sprint execution report: `ai-sprints/167/40-sprint-execution.md` created.

### Active Risks / Blockers

- No active blockers on completed wave.
- Sprint is not closed: PYPOST-421/422/423/424 are still in `To Do`.

### Next Action

- **analyst** → prepare independent task flow for PYPOST-421..424 (step 1 artifacts per task).
- Keep **STEP 3** open until all sprint-scope issues are finished or formally de-scoped.
