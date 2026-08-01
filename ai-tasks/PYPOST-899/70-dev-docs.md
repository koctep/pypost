# PYPOST-899: Dev Docs Update

## Summary

Documented live-session ready-event caplog smoke (PYPOST-899) alongside the
existing PYPOST-867 mocked unit proofs and logging catalog.

## Changes

- `doc/dev/agent_e2e.md` — Harness table row for
  `tests/test_agent_e2e_session_ready_logs.py`; packaging ready note distinguishes
  live smoke vs mocked unit proof; troubleshooting row updated
- `doc/dev/logging.md` — Catalog prose links the PYPOST-899 live-session smoke
  module

## Key developer guidance

1. **Fast unit proof (no Qt):**
   `make test PYTEST_ARGS="tests/test_agent_e2e_packaging_logs.py -v"` (PYPOST-867)
2. **Live e2e smoke (offscreen Qt):**
   `make test-agent-e2e PYTEST_ARGS="tests/test_agent_e2e_session_ready_logs.py -v"`
3. Assert under
   `caplog.at_level(logging.INFO, logger="tests._pytest_plugins.agent_e2e")`.
4. Drive fixtures inside caplog via `request.getfixturevalue` when capturing
   setup-time ready logs.

## Validation

- [x] `agent_e2e.md` harness table includes new module
- [x] `agent_e2e.md` distinguishes live vs unit ready-log proofs
- [x] `logging.md` points at live smoke tests
- [x] Roadmap STEP 8 marked complete
