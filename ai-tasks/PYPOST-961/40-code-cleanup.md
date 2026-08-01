# PYPOST-961: Code Cleanup

## Summary

Test-only change; no production code edits.

## Cleanup performed

- Parametrized test reuses hook install/restore pattern from
  `test_dump_hook_failure_logs_warning` — no new helpers.
- Kept PYPOST-912 dedicated RuntimeError test for historical traceability;
  parametrized test also covers RuntimeError (redundant but harmless).
- Module-level `pytestmark` timeout unchanged.

## Files touched

| File | Notes |
| --- | --- |
| `tests/test_agent_e2e_failure_artifacts.py` | One parametrized test (5 cases) |
| `doc/dev/agent_e2e_failure_artifacts.md` | Tests section |
