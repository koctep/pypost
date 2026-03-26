# Roadmap — PYPOST-85: Private _collections mutation in reload test

**Issue type:** Tech Debt
**Priority:** Medium
**Created:** 2026-03-25

---

## Steps

- [x] 0. **Project Manager** — initialise roadmap & Jira kickoff comment
- [x] 1. **Analyst** — gather requirements → `10-requirements.md`
- [x] 2. **Product Owner** — review `10-requirements.md` for business logic
- [x] 3. **Senior Engineer** — create architecture doc → `20-architecture.md`
- [x] 4. **Team Lead** — review `20-architecture.md`
- [x] 5. **Junior Engineer** — implement fix (replace `_collections` mutation with
       public API or constructor initialisation in `test_request_manager.py`)
- [x] 5a. **Senior Engineer** — review implementation
- [x] 5b. **Junior Engineer** — code cleanup → `40-code-cleanup.md`
- [x] 6. **Senior Engineer** — observability review → `50-observability.md`
- [x] 7. **Team Lead** — tech-debt analysis → `60-review.md`, dev docs → `70-dev-docs.md`,
       final commit
- [x] 8. **Project Manager** — final Jira closure & roadmap sync

---

## Project Manager Update — 2026-03-25 (phase: KICKOFF)

**Completed milestones:**
- Step 0 (PM kickoff): done — roadmap initialised, Jira moved to In Progress

**Active risks/blockers:**
- None identified at kickoff. PYPOST-89 (CI), PYPOST-88 (cov threshold), PYPOST-83 (fragile
  call_args), and PYPOST-84 (ScriptExecutor mock) are all committed and green — test
  infrastructure is stable for this fix.

**Context:**
- Issue source: `ai-tasks/PYPOST-52/60-review.md` (item MEDIUM-3)
- Location: `tests/test_request_manager.py:88`
- Problem: `self.storage._collections = [col]` directly mutates a private attribute of
  `FakeStorageManager` before calling `reload_collections()`. If the attribute is renamed
  or the fake is refactored, the test breaks silently with wrong behaviour rather than an
  error.
- Recommended fix: initialise `FakeStorageManager` with the desired collections from the
  start, or add a `set_collections()` helper to `FakeStorageManager`.

**Next action:** Closed — `seed_collections` on `FakeStorageManager`; reload test updated.
