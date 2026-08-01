# PYPOST-907: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Decision **DEFER after evidence**: keep intentional Python 3.11 double-run of
agent e2e (main `test` matrix + dedicated `agent-e2e` job). Actions timings
are published; ENABLE threshold recorded. No CI selection change. Items
below are non-blocking. **Do not create Jira tickets in this step** — list
unticketed follow-ups only for orchestrator Phase D.

## Shortcuts Taken

- **Sample size thin (n=2)** Actions runs with job `agent-e2e`; older runs in
  the window predated the job.
- **Did not expand `agent-e2e` to 3.11/3.13** (ENABLE sketch only).
- **Local pack wall-clock not used as proof** — a timed
  `make test-agent-e2e` with `PYTEST_ARGS` accidentally ran a near-full suite.
- **Full `make check` / full suite not re-run.** Validated the lock (2
  passed) + harness-table doc guard.

## Code Quality Issues

- None that block close. Optional: shared YAML parser helper if more CI
  locks appear (today: substring checks).

## Missing Tests

| Scenario | Status |
| --- | --- |
| Docs name PYPOST-873/907 + intentional double-run + evidence + DEFER after evidence | Covered |
| Workflow has `agent-e2e` and does not exclude `agent_e2e` | Covered |
| Automated scrape of live Actions durations into CI | Not covered — follow-up |
| ENABLE trim recipe (matrix `-m` + expanded job) | Not implemented — DEFER |

Timeout markers: module `pytestmark` on the lock test. **No timeout-marker
blockers.**

## Performance Concerns

- Intentional 3.11 overlap remains (~172s dedicated pack step in sample run
  #21). Wall clock still dominated by main matrix. Revisit per ENABLE
  threshold in `doc/dev/testing.md`.

## Follow-Up Tasks

1. **ENABLE CI cost trim when ENABLE threshold is met**
   - Priority: Low
   - When dedicated `make test-agent-e2e` ≥6m across ≥3 green runs (or other
     documented triggers), exclude `agent_e2e` from the main matrix **with**
     a 3.13 coverage plan; update lock + docs for ENABLE.
   - Jira: [PYPOST-930](https://pypost.atlassian.net/browse/PYPOST-930)

2. **Optional: automate CI duration evidence capture**
   - Priority: Lowest
   - Script or docs checklist to refresh the evidence table from Actions API
     (may absorb or close [PYPOST-908](https://pypost.atlassian.net/browse/PYPOST-908)
     once maintainers confirm published numbers suffice).
   - Jira: [PYPOST-931](https://pypost.atlassian.net/browse/PYPOST-931) (related existing PYPOST-908)

## Blocker Verdict

**SAFE TO CLOSE** — acceptance met via evidence + DEFER scaffolding; no
blockers relative to DoD.
