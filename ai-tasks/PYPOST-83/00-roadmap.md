# Roadmap — PYPOST-83: Fix Fragile Positional call_args in test_request_service

**Issue type:** Tech Debt
**Priority:** Medium
**Created:** 2026-03-25

---

## Steps

- [x] 0. **Project Manager** — initialise roadmap & Jira kickoff comment
- [x] 1. **Analyst** — gather requirements → `10-requirements.md`
- [x] 2. **Product Owner** — review `10-requirements.md` for business logic
- [x] 3. **Senior Engineer** — create architecture doc → `20-architecture.md`
- [x] 4. **Team Lead** — review `20-architecture.md` *(approved, no blockers)*
- [x] 5. **Junior Engineer** — implement fix (keyword args in `request_service.py`
       + `.kwargs` assertions in `test_request_service.py`)
- [x] 5a. **Senior Engineer** — review implementation *(verified: 23 tests passing)*
- [x] 5b. **Junior Engineer** — code cleanup → `40-code-cleanup.md`
- [x] 6. **Senior Engineer** — observability review → `50-observability.md`
       *(no new instrumentation required; existing coverage confirmed complete)*
- [x] 7. **Team Lead** — tech-debt analysis → `60-review.md`, dev docs → `70-dev-docs.md`,
       final commit
- [ ] 8. **Project Manager** — final Jira closure & roadmap sync

---

## Project Manager Update — 2026-03-25 (refresh: observability_ready)

**Completed milestones:**
- Step 0 (PM kickoff): done
- Step 1 (Analyst): `10-requirements.md` complete — scope, FRs, NFRs, and acceptance criteria defined
- Step 2 (Product Owner review): requirements confirmed
- Step 3 (Senior Engineer): `20-architecture.md` complete — two-file refactor plan defined
- Step 4 (Team Lead): architecture reviewed, approved with no blockers
- Step 5 (Junior Engineer): implementation complete — `request_service.py` uses keyword args;
  `test_request_service.py` uses `.kwargs["name"]` assertions
- Step 5a (Senior Engineer): implementation review done — 23 tests passing, no regressions
- Step 5b (Junior Engineer): `40-code-cleanup.md` complete — no style or coverage issues
- Step 6 (Senior Engineer): `50-observability.md` complete — no new instrumentation required;
  existing logging, metrics, and alerting fully cover the refactored execution path

**Active risks/blockers:** None

**Next action:** Team Lead → tech-debt analysis (`60-review.md`), dev docs (`70-dev-docs.md`),
and final commit (Step 7)
