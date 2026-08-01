# PYPOST-912: Dev Docs Update

## Summary

Documented caplog proof for `agent_session_failure_dump_hook_failed` (PYPOST-912)
alongside existing failure-artifact test coverage and the logging catalog.

## Changes

- `doc/dev/agent_e2e_failure_artifacts.md` — Tests section notes in-process
  caplog proof for hook-failed WARNING
- `doc/dev/logging.md` — Catalog prose links caplog proof in failure-artifacts
  tests module

## Key developer guidance

1. **Caplog proof (in-process):**
   `make test-agent-e2e PYTEST_ARGS="tests/test_agent_e2e_failure_artifacts.py::test_dump_hook_failure_logs_warning -v"`
2. Assert under
   `caplog.at_level(logging.WARNING, logger="pypost.agent.lifecycle")`.
3. Install a raising hook via `set_agent_session_failure_dump_hook`; restore
   with `make_direct_session_failure_dump_hook()` in `finally`.

## Validation

- [x] `agent_e2e_failure_artifacts.md` Tests section mentions caplog proof
- [x] `logging.md` points at caplog test
- [x] Roadmap STEP 8 marked complete
