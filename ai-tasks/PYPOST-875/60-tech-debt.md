# PYPOST-875: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE (non-blockers only)

Direct `AgentAppSession` constructions now auto-dump masked failure
artifacts via an optional `__exit__` hook installed by the agent e2e
plugin. Fixture makereport path unchanged. Docs and subprocess proof
cover the contract. Items below are non-blocking follow-ups — record
here only (no Jira in this run).

## Shortcuts Taken

- **Module-global dump hook** on `AgentAppSession` rather than a formal
  plugin registry API — adequate for one harness plugin; fine to replace
  later if multiple consumers appear.
- **No dedicated unit test for ContextVar bind/clear** — covered
  indirectly by the direct-construction subprocess proof.
- **Asserts after the `with` block still have no live session** — dump
  only when failure happens while the session context is active (same
  timing constraint as the parent debt note).

## Code Quality Issues

- **BLE001** retained in lifecycle dump-hook wrapper and dump helper
  (intentional best-effort). Narrowing tracked by PYPOST-876 for the
  helper; lifecycle wrapper could follow the same tuple later.
- **`session_fixture` field name** is slightly overloaded for
  provenance=`direct` (not a fixture). Rename would be a diagnostics
  schema bump — deferred.

## Missing Tests

| Scenario | Status |
| --- | --- |
| Direct construction dumps on assert fail | Covered (subprocess) |
| Fixture makereport dump still works | Covered (existing subprocess) |
| Hook unset ⇒ no dump outside plugin | Implicit; no dedicated unit |
| Caplog for `agent_session_failure_dump_hook_failed` | Not asserted |
| Nested concurrent sessions dump selection | Not covered (sequential only) |

No timeout-marker blockers.

## Performance Concerns

None relative to DoD. Dump runs only on exceptional `__exit__` or
fixture call failure; success paths unchanged.

## Follow-up Tasks

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Narrow dump helper exception types | [PYPOST-876](https://pypost.atlassian.net/browse/PYPOST-876) |
| CI upload of failure artifacts | [PYPOST-874](https://pypost.atlassian.net/browse/PYPOST-874) |
| Parent failure artifacts | [PYPOST-860](https://pypost.atlassian.net/browse/PYPOST-860) |

### NON-BLOCKER

#### Caplog proof for dump-hook failure WARNING

- **Priority:** Lowest
- **Description:** Unit-test that a raising dump hook logs
  `agent_session_failure_dump_hook_failed` and still shuts down /
  re-raises the original exception.
- **Files:** `tests/test_agent_e2e_failure_artifacts.py`,
  `pypost/agent/lifecycle.py`
- **Jira:** [PYPOST-912](https://pypost.atlassian.net/browse/PYPOST-912)

#### Rename diagnostics `session_fixture` → `session_source`

- **Priority:** Lowest
- **Description:** Clarify provenance field for `direct` vs packaging
  fixture names; requires doc + lock updates.
- **Files:** `pypost/fixtures/agent_e2e_failure.py`,
  `doc/dev/agent_e2e_failure_artifacts.md`, tests
- **Jira:** [PYPOST-913](https://pypost.atlassian.net/browse/PYPOST-913)
