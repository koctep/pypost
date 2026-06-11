# PYPOST-332: Technical Debt Analysis

## Shortcuts Taken

None. Tests follow existing presenter fake patterns; no production shortcuts.

## Code Quality Issues

None introduced.

## Missing Tests

- No `MainWindow`-level GUI test for delete context menu → tab close (deferred to PYPOST-338).
- No test asserting `close_tabs_for_deleted_requests` log output (low value; behavior covered
  by tab count and state assertions).

## Performance Concerns

None. Test suite additions are fast unit/integration tests with in-memory fakes.

## Follow-up Tasks

None filed from this task. Related debt remains in parent PYPOST-35 follow-ups:
- PYPOST-338 — GUI/integration tests for context menu + confirmation + model refresh.
- PYPOST-331 — delete metric emission tests.
