# PYPOST-961: Dedicated hook best-effort units per exception type

## Summary

Follow-up to [PYPOST-914](https://pypost.atlassian.net/browse/PYPOST-914): add
parametrized or individual tests that install dump hooks raising each member of
`DUMP_BEST_EFFORT_ERRORS` and assert WARNING without propagation on the
lifecycle hook path. Scope is the hook wrapper only — dump-helper per-type
units are [PYPOST-915](https://pypost.atlassian.net/browse/PYPOST-915).

## User Stories

- **As a harness maintainer**, I want a unit per best-effort exception type on
  the lifecycle hook path so tuple regressions fail CI immediately.
- **As a test author**, when a hook raises an expected best-effort kind, the
  original assert failure remains primary — hook WARNING only.

## Functional Requirements

- FR1: Each member of `DUMP_BEST_EFFORT_ERRORS` has hook-path coverage:
  `OSError`, `RuntimeError`, `TypeError`, `ValueError`, `AttributeError`.
- FR2: Hook best-effort failures log
  `agent_session_failure_dump_hook_failed error=<ExcType>` and do not
  propagate from `__exit__`.
- FR3: Existing PYPOST-912 / PYPOST-914 hook tests remain green.
- FR4: Developer docs list hook per-type proof.

## Out of Scope

- Dump-helper per-type units (PYPOST-915).
- Production changes to `AgentAppSession.__exit__` (PYPOST-914 done).
- Jira follow-up creation in this run.
- Commit or Jira Done transition (orchestrator skip).

## Acceptance Criteria

- Parametrized or individual tests cover every `DUMP_BEST_EFFORT_ERRORS`
  member on the lifecycle hook path.
- Caplog asserts WARNING + exc type name; original `AssertionError` propagates.
- `doc/dev/agent_e2e_failure_artifacts.md` Tests section updated.

## Business Need

Close lowest-priority debt from PYPOST-914 so hook best-effort contract is
locked per type, not only via implicit tuple membership and a single
`RuntimeError` smoke test.
