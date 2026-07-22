# PYPOST-873: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Decision **DEFER**: keep intentional Python 3.11 double-run of agent e2e
(main `test` matrix + dedicated `agent-e2e` job). Docs and a workflow/doc
lock encode the decision. No CI selection change. Items below are
non-blocking. **Do not create Jira tickets in this step** — list unticketed
follow-ups only.

## Shortcuts Taken

- **Did not measure billable CI minutes** on a live Actions run; decision
  relies on parent “until painful” guidance plus local collect size (~48
  agent e2e tests vs ~1782 suite).
- **Did not expand `agent-e2e` to a 3.11/3.13 matrix** as an ENABLE
  prerequisite sketch beyond docs.
- **Full `make check` / full suite not re-run.** Validated the new lock
  (2 passed) + harness-table doc guard.

## Code Quality Issues

- None that block close. Optional: static parse of workflow jobs via a
  shared YAML helper if more CI locks appear (today: simple substring
  checks).

## Missing Tests

| Scenario | Status |
| --- | --- |
| Docs name PYPOST-873 + intentional double-run + revisit when | Covered |
| Workflow has `agent-e2e` and does not exclude `agent_e2e` | Covered |
| Live CI minute / duration regression gate | Not covered — follow-up |
| ENABLE trim recipe (matrix `-m` + expanded job) | Not implemented — DEFER |

Timeout markers: module `pytestmark` on the lock test. **No timeout-marker
blockers.**

## Performance Concerns

- Intentional 3.11 overlap remains. Dedicated job still pays Qt +
  `make install`; main matrix pays agent e2e execution inside an already
  warm pytest process. Revisit if either surface becomes painful.

## Follow-Up Tasks

1. **ENABLE CI cost trim when pain is evidenced**
   - Priority: Low
   - Exclude `agent_e2e` from the main matrix **only with** a plan that
     preserves 3.13 coverage (e.g. expand `agent-e2e` matrix), then update
     `tests/test_agent_e2e_ci_double_run_doc.py` and docs.
   - Jira: [PYPOST-907](https://pypost.atlassian.net/browse/PYPOST-907)

2. **Optional: record CI duration evidence for the overlap**
   - Priority: Lowest
   - Capture a few Actions runs’ `test` vs `agent-e2e` timings to ground
     the next ENABLE/DEFER call with numbers.
   - Jira: [PYPOST-908](https://pypost.atlassian.net/browse/PYPOST-908)

## Blocker Verdict

**SAFE TO CLOSE** — acceptance criteria met; no blockers relative to DoD.
