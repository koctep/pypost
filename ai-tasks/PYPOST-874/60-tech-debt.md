# PYPOST-874: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Decision **ENABLE**: job `agent-e2e` uploads `artifacts/agent_e2e/` on
failure as Actions artifact `agent-e2e-failure-artifacts`. Docs and a
workflow/doc lock encode the contract. Items below are non-blocking.
**Do not create Jira tickets in this step** — list unticketed follow-ups
only.

## Shortcuts Taken

- **Did not add upload to the main `test` matrix** when agent e2e fails
  there (ticket scoped to dedicated job only).
- **Did not add `retention-days`** — uses Actions default retention.
- **Full `make check` / full suite not re-run.** Validated the new lock
  (2 passed) + PYPOST-873 double-run lock (2 passed).
- **Job-block parser in the lock test is substring/heuristic** (same
  style as other CI doc locks), not a full YAML AST.

## Code Quality Issues

- None that block close. Optional later: shared YAML helper if more CI
  locks appear.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Docs name PYPOST-874 + ENABLE + artifact name | Covered |
| Workflow uploads path with `if: failure()` | Covered |
| Live Actions run proves downloadable zip | Not covered — follow-up |
| Main matrix failure upload | Not implemented — follow-up |

Timeout markers: module `pytestmark` on the lock test. **No timeout-marker
blockers.**

## Performance Concerns

- None. Upload runs only on failure; dumps are small JSON trees.

## Follow-Up Tasks

1. **Optional: upload agent e2e dumps from main `test` matrix on failure**
   - Priority: Low
   - When agent e2e fails inside `-m "not slow"`, upload
     `artifacts/agent_e2e/` (name per Python version) so 3.13 matrix
     failures are also downloadable.
   - Files: `.github/workflows/test.yml`, docs, lock test
   - Jira: [PYPOST-909](https://pypost.atlassian.net/browse/PYPOST-909)

2. **Optional: set explicit `retention-days` on failure artifact**
   - Priority: Lowest
   - Cap storage if artifact retention defaults grow too long for the org.
   - Files: `.github/workflows/test.yml`
   - Jira: [PYPOST-910](https://pypost.atlassian.net/browse/PYPOST-910)

3. **Optional: one-time CI proof comment after first red `agent-e2e` with dumps**
   - Priority: Lowest
   - Confirm Artifacts UI shows `agent-e2e-failure-artifacts` on a real
     failure (or staged fail) and note in docs if UX differs.
   - Jira: [PYPOST-911](https://pypost.atlassian.net/browse/PYPOST-911)

## Blocker Verdict

**SAFE TO CLOSE** — acceptance criteria met; no blockers relative to DoD.
