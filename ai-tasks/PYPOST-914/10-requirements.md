# PYPOST-914: Narrow lifecycle dump-hook exception types

## Summary

Follow-up to [PYPOST-876](https://pypost.atlassian.net/browse/PYPOST-876): replace
broad `except Exception` around `_failure_dump_hook` in
`AgentAppSession.__exit__` with a documented best-effort tuple aligned with
the dump helper. Unexpected hook failures must propagate instead of being
logged and swallowed.

## User Stories

- **As a maintainer**, when the dump hook raises an unexpected exception type,
  I want it to propagate so hook bugs are visible in the traceback rather
  than hidden behind a generic WARNING.
- **As a test author**, when dump I/O fails with an expected best-effort kind
  (e.g. `RuntimeError`), I still want the original test failure to remain
  primary — lifecycle logs `agent_session_failure_dump_hook_failed` and
  continues shutdown.

## Functional Requirements

- FR1: Lifecycle dump-hook wrapper catches only a documented best-effort tuple
  (aligned with `_DUMP_BEST_EFFORT_ERRORS` from PYPOST-876).
- FR2: Exceptions outside that tuple propagate from `__exit__` (Python chains
  them with the original test exception as `__context__`).
- FR3: Existing caplog proof for `RuntimeError` hook failure (PYPOST-912)
  remains green.
- FR4: Docs and tests updated to describe the narrowed catch set.

## Out of Scope

- Changing `_DUMP_BEST_EFFORT_ERRORS` in the dump helper module.
- Extracting a shared constant module (optional follow-up).
- Jira follow-up creation in this run.

## Acceptance Criteria

- Lifecycle dump-hook catch tuple narrowed; `# noqa: BLE001` removed.
- Unexpected exceptions (e.g. `LookupError`) propagate from hook wrapper.
- `test_dump_hook_propagates_unexpected_exception` green; PYPOST-912 test green.
- `doc/dev/agent_e2e_failure_artifacts.md` documents hook catch set.

## Business Need

Close lowest-priority debt from PYPOST-876 so lifecycle and dump helper share
the same intentional best-effort contract and unexpected bugs surface clearly.
