# PYPOST-908: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: timing notes (job durations / overlap cost) are published in
`doc/dev/testing.md`, discoverable from `agent_e2e.md` and the harness table,
cited in `ai-tasks/PYPOST-908/*`, and locked so PYPOST-908 remains linked.
No invented timings. No workflow change. Items below are non-blocking.
**Do not create Jira tickets in this step** — list follow-ups only (Phase D
orchestrator may skip creation when links already exist).

## Shortcuts Taken

- **Did not re-scrape Actions** — reused PYPOST-907 / `testing.md` numbers
  (n=2 sample still thin).
- **Did not add Actions refresh automation** — owned by PYPOST-931.
- **Did not ENABLE cost trim** — threshold unchanged; PYPOST-930.
- **Full `make check` / full suite not re-run** — targeted lock (2 passed).

## Code Quality Issues

- None that block close. Optional: shared doc-anchor constants if more CI
  ticket locks appear (today: module-local `_DOC_ANCHOR_*`).

## Missing Tests

| Scenario | Status |
| --- | --- |
| Docs name PYPOST-873/907/908 + intentional double-run + evidence + DEFER | Covered |
| PYPOST-908 in both `testing.md` and `agent_e2e.md` | Covered |
| Workflow keeps dual coverage (`agent-e2e`; no `not agent_e2e`) | Covered |
| Automated scrape of live Actions durations | Not covered — PYPOST-931 |
| ENABLE trim recipe | Not implemented — PYPOST-930 |

Timeout markers: module `pytestmark` on the lock test. **No timeout-marker
blockers.**

## Performance Concerns

- Intentional 3.11 overlap remains (~172s dedicated pack step in sample run
  #21). Wall clock still dominated by main matrix. Revisit per ENABLE
  threshold in `doc/dev/testing.md`.

## Follow-Up Tasks

1. **ENABLE CI cost trim when ENABLE threshold is met**
   - Priority: Low
   - Already ticketed — do not recreate.
   - Jira: [PYPOST-930](https://pypost.atlassian.net/browse/PYPOST-930)

2. **Automate CI duration evidence capture / refresh**
   - Priority: Lowest
   - Script or checklist to refresh the evidence table from Actions API.
   - Already ticketed — may absorb any residual “refresh” work from 908.
   - Jira: [PYPOST-931](https://pypost.atlassian.net/browse/PYPOST-931)

## Blocker Verdict

**SAFE TO CLOSE** — discoverability + lock satisfy acceptance; no blockers
relative to DoD. No new Jira Debt issues required (930/931 already linked).
