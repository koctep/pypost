# PYPOST-867: Dev Docs Update

## Summary

Documented packaging ready-event caplog coverage (PYPOST-867) next to the
existing session fixture / logging catalog docs. No new `doc/dev/` file was
required — `agent_e2e.md` and `logging.md` already described the event; this
step points at the automated proof.

## Changes

- `doc/dev/agent_e2e.md` — Shared session fixtures note blank/seeded
  `agent_e2e_fixture_ready` + `tests/test_agent_e2e_packaging_logs.py`;
  Troubleshooting row for ready-log regressions
- `doc/dev/logging.md` — Catalog prose links the PYPOST-867 packaging-logs
  caplog module

No user-facing docs (test-harness / developer observability only).
`doc/dev/logging.md` already catalogs `agent_e2e_fixture_ready` (PYPOST-858).

## Key developer guidance

1. Drive packaging fixtures (or mock session boundary as in the unit proof).
2. Assert under
   `caplog.at_level(logging.INFO, logger="tests._pytest_plugins.agent_e2e")`.
3. Expect `"agent_e2e_fixture_ready mode=blank"` and/or `mode=seeded`.
4. Run:
   `make test PYTEST_ARGS="tests/test_agent_e2e_packaging_logs.py -v"`.

## Validation

- [x] `agent_e2e.md` documents ready-log proof + troubleshooting
- [x] `logging.md` points at packaging-logs tests
- [x] Artifact `70-dev-docs.md` created
- [x] Roadmap STEP 8 marked complete
