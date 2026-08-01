# PYPOST-915: Dev Docs Update

## Summary

Documented dedicated OSError and AttributeError best-effort unit coverage
(PYPOST-915) in the failure-artifacts developer guide Tests section.

## Changes

- `doc/dev/agent_e2e_failure_artifacts.md` — Tests section lists
  `OSError` and `AttributeError` alongside existing `RuntimeError` proof

## Key developer guidance

1. **OSError write path:**
   `make test PYTEST_ARGS="tests/test_agent_e2e_failure_artifacts.py::test_dump_best_effort_on_oserror -v"`
2. **AttributeError capture path:**
   `make test PYTEST_ARGS="tests/test_agent_e2e_failure_artifacts.py::test_dump_best_effort_on_attribute_error -v"`
3. Assert under
   `caplog.at_level(logging.WARNING, logger="pypost.fixtures.agent_e2e_failure")`.

## Validation

- [x] `agent_e2e_failure_artifacts.md` Tests section mentions OSError /
  AttributeError dedicated units
- [x] Roadmap STEP 8 marked complete
