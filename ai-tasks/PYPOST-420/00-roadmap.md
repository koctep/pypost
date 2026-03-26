# PYPOST-420 — Logger Accumulation in AlertManager

> Sprint: 167
> Date: 2026-03-26
> Type: Tech Debt (child of PYPOST-402)
> Priority: Medium
> Methodology: Top-Down (Requirements → Architecture → Dev → Cleanup → Observability →
> Review → Docs → Commit)

## Summary

`AlertManager.__init__` unconditionally calls `logging.getLogger().addHandler()` on every
instantiation. This causes the root logger to accumulate duplicate handlers, resulting in
log-line multiplication proportional to the number of `AlertManager` instances created.

---

## Deliverables Checklist

- [x] **10-requirements.md** — Analyst gathers requirements ✓
- [x] **20-architecture.md** — Senior Engineer creates architecture ✓
- [x] **40-code-cleanup.md** — Junior Engineer performs code cleanup ✓
- [x] **50-observability.md** — Senior Engineer implements observability ✓
- [x] **60-review.md** — Team Lead tech-debt analysis ✓
- [x] **70-dev-docs.md** — Team Lead dev docs ✓
- [x] **Final commit** — Team Lead commits ✓

---

## Step Progress

| Step | Role | Deliverable | Status |
|------|------|-------------|--------|
| 1 | Analyst | `10-requirements.md` | Done |
| 2 | Product Owner | Requirements review | Done |
| 3 | Senior Engineer | `20-architecture.md` | Done |
| 4 | Team Lead | Architecture review | Done |
| 5 | Junior Engineer | Implementation (inner loop) | Done |
| 5b | Junior Engineer | `40-code-cleanup.md` | Done |
| 6 | Senior Engineer | `50-observability.md` | Done |
| 7 | Team Lead | `60-review.md` | Done |
| 7b | Team Lead | `70-dev-docs.md` | Done |
| 7c | Team Lead | Final commit | Done |
| 8 | Project Manager | Jira closure | To Do |

---

## Context

- **Root cause**: Each `AlertManager()` call appends a new handler to the root logger via
  `logging.getLogger().addHandler()`, with no guard against duplicate registration.
- **Impact**: Log lines are duplicated proportionally to instantiation count, polluting logs
  and potentially masking real events.
- **Execution order in Sprint 167**: **PYPOST-420** (this issue) → PYPOST-418 → PYPOST-419.
  This is the sprint entry point — a low-risk, isolated fix that unblocks subsequent wiring.

---

## Project Manager Update

**Date**: 2026-03-26
**Phase**: `observability_ready` — Observability complete; awaiting Team Lead review, dev docs,
and final commit.

### Completed Milestones

- Sprint 167 backlog confirmed; PYPOST-420 is the sprint entry point
  (execution order: PYPOST-420 → PYPOST-418 → PYPOST-419).
- Roadmap initialized.
- `10-requirements.md` complete (analyst) — 6 FRs, 6 ACs, root-cause analysis of CPython `id()`
  reuse / handler-FD leak / missing regression test; affected files identified.
- Product Owner requirements review: approved.
- `20-architecture.md` complete (senior_engineer) — handler guard in `__init__`, `close()`,
  `__enter__`/`__exit__`, new `TestAlertManagerAccumulation` test class; 2-file scope confirmed,
  no new dependencies.
- Team Lead architecture review: approved.
- Implementation complete (junior_engineer) — handler guard, `close()`, `__enter__`/`__exit__`
  added to `alert_manager.py`; `TestAlertManagerAccumulation` added to `test_alert_manager.py`.
- `40-code-cleanup.md` complete — style/standards compliance verified; all 17 tests pass
  (15 pre-existing + 2 new regression tests).
- `50-observability.md` complete (senior_engineer) — 6 log events instrumented:
  `alert_manager_init` (DEBUG), `alert_manager_stale_handlers_evicted` (WARNING),
  `alert_emitted` (WARNING, pre-existing), `alert_webhook_ok` (DEBUG),
  `alert_webhook_failed` (WARNING, pre-existing), `alert_manager_close` (DEBUG). No new
  dependencies. Stale-eviction warning exercised by existing regression test.

### Active Risks / Blockers

None. All AC-1–AC-6 satisfied; test suite green (17/17).

### Next Action

- **Owner**: `team_lead` → create `60-review.md` (tech-debt analysis), `70-dev-docs.md`
  (dev docs), and perform the final commit.
- On commit completion → `project_manager` for Jira closure.
