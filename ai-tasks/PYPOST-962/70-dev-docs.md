# PYPOST-962: Dev Docs Update

## Summary

Documented dedicated TypeError and ValueError best-effort unit coverage
(PYPOST-962) in the failure-artifacts developer guide Tests section.

## Changes

- `doc/dev/agent_e2e_failure_artifacts.md` — Tests section lists
  `TypeError` and `ValueError` alongside existing dump-helper proof

## Key developer guidance

1. **TypeError capture path:**
   `make test PYTEST_ARGS="tests/test_agent_e2e_failure_artifacts.py::test_dump_best_effort_on_type_error -v"`
2. **ValueError capture path:**
   `make test PYTEST_ARGS="tests/test_agent_e2e_failure_artifacts.py::test_dump_best_effort_on_value_error -v"`
3. Assert under
   `caplog.at_level(logging.WARNING, logger="pypost.fixtures.agent_e2e_failure")`.

## Validation

- [x] `agent_e2e_failure_artifacts.md` Tests section mentions TypeError /
  ValueError dedicated units
- [x] Roadmap STEP 8 marked complete
