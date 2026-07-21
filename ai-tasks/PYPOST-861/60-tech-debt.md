# PYPOST-861: Technical Debt Analysis

## Shortcuts Taken

- Dedicated CI job runs on **Python 3.11 only** (mirrors
  `make-install-smoke`) while the main matrix still covers agent_e2e on
  3.11 + 3.13 via `-m "not slow"`. Slight overlap on 3.11 is accepted for
  a named make gate.
- `make test-agent-e2e` still depends on `venv-otel` only (not `venv-test`);
  CI uses `make install` first so pytest is present. Same latent pattern as
  `make test` / `make test-cov` dependency split.

## Code Quality Issues

- None material in the new smoke tests.

## Missing Tests

- No workflow YAML schema test (project does not generally unit-test
  `.github/workflows/*.yml`). Documented + exercised by CI itself.
- Optional: assert CI workflow file contains the `agent-e2e` job name
  (static string check) — low value vs reading the workflow in review.

## Performance Concerns

- Agent e2e pack runs twice on Python 3.11 (main `test` job + `agent-e2e`
  job). Acceptable for first-class gating; could later narrow main job
  selection if CI minutes become a problem.

## PYPOST-854 Absorption

| Item | Status |
| --- | --- |
| TD-1 marker `agent_e2e` | Delivered by PYPOST-858 (not re-owned) |
| TD-2 makefile smoke | Absorbed here (`test_makefile.py`) |
| TD-3 optional CI step | Absorbed here (`agent-e2e` job) |

Recommend closing or linking
[PYPOST-854](https://pypost.atlassian.net/browse/PYPOST-854) as superseded
after this story merges (process follow-up; not a code blocker).

## Follow-Up Debt (NEW tickets needed)

1. **Make test targets depend on `venv-test` (or document install-first)**
   - Priority: Low
   - `test` / `test-agent-e2e` assume pytest already in `.venv`; CI/docs use
     `make install` first. Consider adding `venv-test` as a prerequisite or
     documenting the install-first contract in one place.
   - Jira: [PYPOST-872](https://pypost.atlassian.net/browse/PYPOST-872)

2. **Close / supersede PYPOST-854 after 861 merge**
   - Priority: Low (process)
   - Link 854 → 861 and close debt once make smoke + CI job are on main.
   - Jira: [PYPOST-854](https://pypost.atlassian.net/browse/PYPOST-854) (in sprint; resolve next)

3. **Optional CI cost trim: skip agent_e2e in main matrix when dedicated job exists**
   - Priority: Low
   - Only if double-run minutes become painful; keep dual coverage until then.
   - Jira: [PYPOST-873](https://pypost.atlassian.net/browse/PYPOST-873)

## Blocker Verdict

**SAFE TO CLOSE** — no blockers relative to acceptance criteria. Follow-ups
above are non-blocking debt.
