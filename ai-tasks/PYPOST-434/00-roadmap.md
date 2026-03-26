# PYPOST-434 Roadmap — GitHub Actions: pytest job failed

## Summary

**Type**: Bug
**Priority**: Medium
**Reporter**: Ilya Ashchepkov
**Status**: Done
**Created**: 2026-03-26

## Description

The GitHub Actions CI pipeline's `pytest` job is failing.
Reference run: https://github.com/koctep/pypost/actions/runs/23586633184/job/68681249225

## Deliverables

| # | Artifact                  | Owner             | Status      |
|---|---------------------------|-------------------|-------------|
| 1 | `10-requirements.md`      | analyst           | done        |
| 2 | `20-architecture.md`      | senior_engineer   | done        |
| 3 | Code fix (implementation) | junior_engineer   | done        |
| 4 | `40-code-cleanup.md`      | junior_engineer   | done        |
| 5 | `50-observability.md`     | senior_engineer   | done        |
| 6 | `60-review.md`            | team_lead         | done        |
| 7 | `70-dev-docs.md`          | team_lead         | done        |
| 8 | Final commit              | team_lead         | done        |

## Phase Checklist

- [x] Kickoff & roadmap initialized (project_manager)
- [x] Requirements gathered (analyst)
- [x] Requirements reviewed (product_owner)
- [x] Architecture designed (senior_engineer)
- [x] Architecture reviewed (team_lead)
- [x] Implementation (junior_engineer)
- [x] Code cleanup (junior_engineer)
- [x] Observability (senior_engineer)
- [x] Tech debt review & dev docs (team_lead)
- [x] Final commit (team_lead)
- [x] Jira closure (project_manager)

## Project Manager Update — 2026-03-26 (requirements_ready)

### Completed Milestones
- Jira issue PYPOST-434 created and triaged (Bug, Medium priority).
- Roadmap initialized; task directory scaffolded.
- Analyst completed `10-requirements.md`: root cause confirmed as missing `pythonpath = .`
  in `pytest.ini`; 26 collection errors, 0 tests run in CI; 277 tests pass locally with
  `PYTHONPATH` set; fix is a single-line `pytest.ini` change.

### Active Risks / Blockers
- None currently blocking. Fix is straightforward and well-scoped.
- Risk (`pythonpath` interaction with other `pytest.ini` keys): addressed in architecture;
  implementation verified locally.

---

## Project Manager Update — 2026-03-26 (implementation_done)

### Completed Milestones
- Step 3: Added `pythonpath = .` under `[pytest]` in `pytest.ini` per `20-architecture.md`.
- Local verification (no `PYTHONPATH`): `pytest tests/ --collect-only -q` → 277 collected, exit 0;
  full `pytest tests/` → 277 passed (2 pre-existing `DeprecationWarning` in UI tests, unrelated).

### Next Action
- **senior_engineer**: Step 5 — `50-observability.md`.

---

## Project Manager Update — 2026-03-26 (code_cleanup_done)

### Completed Milestones
- `40-code-cleanup.md`: `pytest.ini` hygiene confirmed; flake8 baseline on `pypost` +
  `tests` documented (pre-existing issues, out of scope for this ticket).

### Next Action
- **team_lead**: Step 6 — `60-review.md` and step 7 — `70-dev-docs.md`.

---

## Project Manager Update — 2026-03-26 (observability_done)

### Completed Milestones
- `50-observability.md`: Documented CI/pytest observability; no code or workflow edits
  (fix unblocks existing junit, coverage, and job summary).

### Next Action
- **project_manager**: Jira closure notes and final status sync.

---

## Project Manager Update — 2026-03-26 (task_closed)

### Completed Milestones
- `60-review.md`: Tech debt review; no new debt from the ini change.
- `70-dev-docs.md`: `doc/dev/setup.md` — unit test / `pythonpath` guidance;
  `doc/dev/tech-debt/PYPOST-434.md` — flake8 gate and Qt warning follow-ups.
- Requirements doc: CI workflow path corrected to `test.yml`; architecture §3.2 aligned with
  committed `pytest.ini`.
- Git commit: `pytest.ini` + `ai-tasks/PYPOST-434/*` + developer docs above.

### Next Action
- None — task closed in Jira and roadmap.

---

## Project Manager Update — 2026-03-26 (jira_closure)

### Completed Milestones
- Jira **PYPOST-434** transitioned to *Done* (transition id 31).
- Closure comment posted with deliverables, commit `c2ebc6a`, and verification reminder for CI
  after push.

### Next Action
- Confirm GitHub Actions green once `c2ebc6a` (or descendant) is on the integration branch.
- Pull PYPOST-434 off the active sprint board if it remains slotted.
