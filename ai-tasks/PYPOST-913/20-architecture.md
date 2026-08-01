# PYPOST-913: Architecture — session_source rename

## Summary

Mechanical rename of the diagnostics provenance field from `session_fixture` to
`session_source` across the dump helper, pytest hook, tests, and docs. No
change to values or dump flow.

## Components

| Location | Change |
| --- | --- |
| `pypost/fixtures/agent_e2e_failure.py` | Kwarg + `_build_diagnostics` dict key |
| `tests/_pytest_plugins/agent_e2e.py` | Pass `session_source=fixture_name` |
| `tests/test_agent_e2e_failure_artifacts.py` | Assert new key; contract test |
| `doc/dev/agent_e2e_failure_artifacts.md` | Field table, examples, troubleshooting |

## Failing Repro Plan (Step 3)

Add `test_diagnostics_uses_session_source_key`: call
`dump_agent_e2e_failure_artifacts(..., session_source="agent_e2e_session")` and
assert `"session_source"` in diagnostics and `"session_fixture"` absent. Fails
on current code (KeyError / wrong key) until Step 4.

## Implementation Plan (Step 4)

1. Rename parameter in `dump_agent_e2e_failure_artifacts` and `_build_diagnostics`.
2. Update dict literal key to `"session_source"`.
3. Update direct hook and makereport call sites.
4. Update all test assertions and kwargs.
5. Run `make test` subset for failure artifacts module.

## Risks

- **Low:** Missed reference in docs or tests — mitigated by repo-wide grep.
- **Low:** External consumers of old JSON key — documented as rename only; no
  dual-write (single key going forward).

## Out of Scope

- `_SESSION_FIXTURE_NAMES` (pytest fixture detection — name stays accurate).
- Historical `ai-tasks/PYPOST-875/*` artifacts (point-in-time records).
