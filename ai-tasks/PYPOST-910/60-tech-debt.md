# PYPOST-910: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Decision **ENABLE**: both agent e2e failure artifact uploads set
`retention-days: 14`. Docs and a workflow/doc lock encode the contract.
Items below are non-blocking. **Do not create Jira tickets in this
step** — list unticketed follow-ups only (Phase D deferred: user forbade
`jira_create_issue` in this run).

## Shortcuts Taken

- **Chose 14 days without org-settings probe** — assumed typical public
  max (≥14); if org max is lower, Actions will clamp or fail upload.
- **Full `make check` / full suite not re-run.** Validated the new lock
  (2 passed) + PYPOST-874/909 locks (4 passed) + `make verify-ai-tasks`.
- **Job-block parser in the lock test is substring/heuristic** (same
  style as sibling CI doc locks), not a full YAML AST.
- **Did not change junit/coverage retention** — out of scope.

## Code Quality Issues

- None that block close. Optional later: share `_job_block` helper with
  874/909 locks (prefer linking existing PYPOST-928 rather than a
  duplicate ticket when Phase D creates issues).

## Missing Tests

| Scenario | Status |
| --- | --- |
| Docs name PYPOST-910 + retention + 14 | Covered |
| Workflow sets `retention-days: 14` on both jobs | Covered |
| Live Actions proves zip expires after 14 days | Not covered — optional |
| Org max < 14 days clamp behavior | Not covered — follow-up if needed |

Timeout markers: module `pytestmark` on the lock test. **No timeout-marker
blockers.**

## Performance Concerns

- None. Retention only shortens storage lifetime; upload path unchanged.

## Follow-Up Tasks

1. **Optional: confirm org/repo Actions max retention ≥ 14**
   - Priority: Lowest
   - If org max is below 14, lower the workflow value (and lock) to match
     or raise the org setting.
   - Files: `.github/workflows/test.yml`, docs, retention lock
   - Jira: *(unticketed — create in Phase D when allowed)*

2. **Optional: extract shared `_job_block` helper for CI workflow locks**
   - Priority: Lowest
   - Deduplicate job-slice heuristics across 874/909/910 lock tests.
   - Prefer linking existing
     [PYPOST-928](https://pypost.atlassian.net/browse/PYPOST-928)
     rather than a duplicate ticket when Phase D runs.

## Blocker Verdict

**SAFE TO CLOSE** — acceptance criteria met; no blockers relative to DoD.
