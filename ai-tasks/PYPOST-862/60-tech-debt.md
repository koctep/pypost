# PYPOST-862: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: mocked StorageManager persist failure, caplog asserts
`agent_e2e_seed_failed`, exception propagates, module timeout marker present.
No production changes; no blockers.

## Shortcuts Taken

- **Mock `save_collection` only.** Failure is forced on the first persist
  call; `save_environments` is asserted not called. Does not separately cover
  environments-save failure after collection succeeds (same `except` path).
- **Co-located under `agent_e2e` marker.** Pure mocked unit shares the module
  with GUI e2e tests for discoverability; slightly heavier marker than a
  dedicated unit module.
- **Used `OSError("disk full")`.** Representative I/O failure; not every
  StorageManager exception type.

## Code Quality Issues

- None material. Test follows sibling failure-artifact caplog style.
- Hardcoded log prefix string matches production / `logging.md` (intentional).

## Missing Tests

| Scenario | Status |
| --- | --- |
| Persist failure → `agent_e2e_seed_failed` + re-raise | Covered (this ticket) |
| Environments-save failure after collection OK | Not covered (same except; optional) |
| Success-path `agent_e2e_seed_completed` caplog | Not covered (optional; out of scope) |

No timeout-marker blockers.

## Performance Concerns

None. Mocked unit test is sub-millisecond; no GUI session.

## Follow-up Tasks

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Optional drive-then-snapshot / resolve proof | [PYPOST-863](https://pypost.atlassian.net/browse/PYPOST-863) |
| Inventory drift guard (code ↔ doc) | [PYPOST-864](https://pypost.atlassian.net/browse/PYPOST-864) |

### NON-BLOCKER

#### Optional environments-save failure branch

- **Priority:** Lowest
- **Description:** Force `save_environments` to raise after
  `save_collection` succeeds; assert same `agent_e2e_seed_failed` + re-raise.
- **Remediation:** One extra mock variant in
  `tests/test_agent_e2e_seed.py` if desired; same except block makes this
  low value.
- **Jira:** unticketed (optional; list for orchestrator — do not create in
  this run per user: Do NOT call Jira)

#### Optional success-path caplog for `agent_e2e_seed_completed`

- **Priority:** Lowest
- **Description:** Assert INFO `agent_e2e_seed_completed` on successful
  `write_agent_e2e_seed` (complements failure C1).
- **Remediation:** Caplog INFO on existing persist inventory test or sibling.
- **Jira:** unticketed (optional; Do NOT call Jira this run)

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | None relative to AC |
| Missing tests with timeout markers | **None** — module `timeout(60)` |
| Deviations from architecture | None — test-only as planned |
| Hardcoded values | Event prefix intentional |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** — FR1–FR4 and DoD satisfied. Remaining items are optional
branch/success caplog polish, not blockers. Unticketed follow-ups noted above
for a later Jira sync (explicitly not created this run).
