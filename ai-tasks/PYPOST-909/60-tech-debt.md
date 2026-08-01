# PYPOST-909: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Decision **ENABLE**: main `test` matrix uploads `artifacts/agent_e2e/`
on failure as Actions artifact
`agent-e2e-failure-artifacts-${{ matrix.python-version }}`. Docs and a
workflow/doc lock encode the contract. Items below are non-blocking.
**Do not create Jira tickets in this step** — list unticketed follow-ups
only (Phase D deferred to orchestrator / this run lists them without
`jira_create_issue`).

## Shortcuts Taken

- **Did not add `retention-days`** — uses Actions default retention
  (already tracked as PYPOST-910 from PYPOST-874).
- **Full `make check` / full suite not re-run.** Validated the new lock
  (2 passed) + PYPOST-874 lock (2 passed) + `make verify-ai-tasks`.
- **Job-block parser in the lock test is substring/heuristic** (same
  style as other CI doc locks), not a full YAML AST.
- **Did not live-prove** a red matrix run downloads the zip (same class
  as PYPOST-911 for `agent-e2e`).

## Code Quality Issues

- None that block close. Optional later: share `_job_block` helper
  between PYPOST-874 and PYPOST-909 lock tests (already ticketed as
  PYPOST-928 for broader CI contract YAML helpers).

## Missing Tests

| Scenario | Status |
| --- | --- |
| Docs name PYPOST-909 + ENABLE + matrix artifact | Covered |
| Workflow uploads path with `if: failure()` on `test` | Covered |
| Live Actions run proves downloadable matrix zip | Not covered — follow-up |
| PYPOST-874 `agent-e2e` upload still green | Covered (sibling lock) |

Timeout markers: module `pytestmark` on the lock test. **No timeout-marker
blockers.**

## Performance Concerns

- None. Upload runs only on failure; dumps are small JSON trees.
  Parallel matrix cells use unique artifact names (v4 requirement).

## Follow-Up Tasks

1. **Optional: one-time CI proof comment after first red matrix cell with dumps**
   - Priority: Lowest
   - Confirm Artifacts UI shows
     `agent-e2e-failure-artifacts-<python>` on a real (or staged) matrix
     failure and note in docs if UX differs from dedicated job.
   - Files: `doc/dev/agent_e2e_failure_artifacts.md` (optional note)
   - Jira: [PYPOST-911](https://pypost.atlassian.net/browse/PYPOST-911) (sprint follow-up for live Artifacts UI proof)

2. **Optional: extract shared `_job_block` helper for CI workflow locks**
   - Priority: Lowest
   - Deduplicate job-slice heuristics across
     `test_agent_e2e_ci_failure_upload_doc.py` and
     `test_agent_e2e_ci_matrix_failure_upload_doc.py`.
   - Prefer linking existing [PYPOST-928](https://pypost.atlassian.net/browse/PYPOST-928)
     rather than a duplicate ticket when Phase D runs.

## Blocker Verdict

**SAFE TO CLOSE** — acceptance criteria met; no blockers relative to DoD.
