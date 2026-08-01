# PYPOST-914: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE (non-blockers only)

Lifecycle dump-hook wrapper catches the same documented best-effort tuple as
the dump helper (PYPOST-876). Unexpected hook failures propagate. Red→green
locks `LookupError` propagation. Docs updated. No Jira follow-ups in this run.

## Shortcuts Taken

- **Duplicated catch tuple** in `lifecycle.py` instead of a shared module —
  avoids circular import with `pypost.fixtures.agent_e2e_failure` (fixtures
  import `AgentAppSession`). Members must stay manually aligned.

## Code Quality Issues

- None blocking.

## Missing Tests

| Scenario | Status |
| --- | --- |
| RuntimeError hook → WARNING (PYPOST-912) | Covered |
| LookupError hook propagates (PYPOST-914) | Covered |
| OSError / TypeError / ValueError / AttributeError hook best-effort | Implicit via tuple; no dedicated unit |
| Shared constant module | Not done (follow-up optional) |

No timeout-marker blockers.

## Performance Concerns

None.

## Follow-up Tasks

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Dump helper narrowing | [PYPOST-876](https://pypost.atlassian.net/browse/PYPOST-876) |
| Hook caplog proof | [PYPOST-912](https://pypost.atlassian.net/browse/PYPOST-912) |
| Dedicated OSError/AttributeError dump units | [PYPOST-915](https://pypost.atlassian.net/browse/PYPOST-915) |

### NON-BLOCKER

#### Extract shared dump best-effort exception tuple

- **Priority:** Lowest
- **Jira:** [PYPOST-960](https://pypost.atlassian.net/browse/PYPOST-960)
- **Description:** Move `_DUMP_BEST_EFFORT_ERRORS` /
  `_DUMP_HOOK_BEST_EFFORT_ERRORS` to a small neutral module (e.g.
  `pypost/agent/e2e_dump_errors.py`) so lifecycle and fixtures share one
  definition without circular imports.
- **Files:** `pypost/agent/lifecycle.py`,
  `pypost/fixtures/agent_e2e_failure.py`

#### Dedicated hook best-effort units per exception type

- **Priority:** Lowest
- **Jira:** [PYPOST-961](https://pypost.atlassian.net/browse/PYPOST-961)
- **Description:** Add parametrized or individual tests that install hooks
  raising each member of `_DUMP_HOOK_BEST_EFFORT_ERRORS` and assert WARNING
  without propagation.
- **Files:** `tests/test_agent_e2e_failure_artifacts.py`
