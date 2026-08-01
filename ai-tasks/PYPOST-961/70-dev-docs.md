# PYPOST-961: Dev Docs Update

## Summary

Documented parametrized hook best-effort per-type coverage (PYPOST-961) in the
failure-artifacts developer guide Tests section.

## Changes

- `doc/dev/agent_e2e_failure_artifacts.md` — Tests section lists parametrized
  hook units for every `DUMP_BEST_EFFORT_ERRORS` member

## Key developer guidance

1. **All hook best-effort types:**
   `make test-agent-e2e PYTEST_ARGS="tests/test_agent_e2e_failure_artifacts.py::test_dump_hook_best_effort_per_type -v"`
2. Assert under
   `caplog.at_level(logging.WARNING, logger="pypost.agent.lifecycle")`.
3. Original `AssertionError` from the `with` body must still propagate.

## Validation

- [x] `agent_e2e_failure_artifacts.md` Tests section mentions PYPOST-961
  parametrized hook units
- [x] Roadmap STEP 8 marked complete
