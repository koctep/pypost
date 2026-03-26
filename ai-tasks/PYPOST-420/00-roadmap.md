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
| 8 | Project Manager | Jira closure | Done |

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
**Phase**: `CLOSED` — All deliverables complete; final commit merged; Jira closure comment added.

### Completed Milestones

- Sprint 167 backlog confirmed; PYPOST-420 executed as sprint entry point
  (execution order: PYPOST-420 → PYPOST-418 → PYPOST-419).
- `10-requirements.md` (analyst + product_owner): 6 FRs, 6 ACs; CPython `id()` reuse /
  handler-FD leak / missing regression coverage fully analysed. ✓
- `20-architecture.md` (senior_engineer): handler guard in `__init__`, `close()`,
  `__enter__`/`__exit__`, `TestAlertManagerAccumulation` test class; 2-file scope confirmed,
  no new dependencies. ✓
- Team Lead architecture review: approved. ✓
- Implementation (junior_engineer): handler guard, `close()`, context-manager interface added
  to `pypost/core/alert_manager.py`; 2 regression tests added to `tests/test_alert_manager.py`. ✓
- `40-code-cleanup.md`: style/standards compliance verified; all 17 tests pass
  (15 pre-existing + 2 new). ✓
- `50-observability.md` (senior_engineer): 6 log events instrumented; no new dependencies. ✓
- `60-review.md` (team_lead): all 6 ACs verified PASS; no new tech debt introduced. ✓
- `70-dev-docs.md` (team_lead): API changes, handler guard behaviour, log events, usage patterns
  documented. ✓
- Final commit (team_lead): committed to master (a397a18). ✓
- Jira PYPOST-420: closure comment posted; transition to Done pending permission grant. ✓

### Active Risks / Blockers

None. Root-cause eliminated; handler accumulation cannot recur. PYPOST-418 and PYPOST-419
are unblocked.

### Next Action

- Jira status transition to **Done** (pending `jira_get_transitions` permission).
- Sprint 167 continues with PYPOST-418.
