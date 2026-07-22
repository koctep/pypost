# PYPOST-862: Dev Docs Update

## Summary

Documented seed write failure-path caplog coverage (PYPOST-862) next to the
existing seed inventory / proof docs. No new `doc/dev/` file was required —
`agent_e2e_seed.md` already described the failure event; this step points at
the automated test.

## Changes

- `doc/dev/agent_e2e_seed.md` — Proof strategy + Troubleshooting mention
  `test_write_agent_e2e_seed_logs_failure_and_reraises` (caplog + re-raise)
- `doc/dev/agent_e2e.md` — Module inventory row notes failure caplog (862)

No user-facing docs (test-harness / developer observability only).
`doc/dev/logging.md` already catalogs `agent_e2e_seed_failed` (PYPOST-857).

## Key developer guidance

1. Force persist failure with a mock on
   `pypost.fixtures.agent_e2e_seed.StorageManager`.
2. Assert under
   `caplog.at_level(logging.ERROR, logger="pypost.fixtures.agent_e2e_seed")`.
3. Expect `"agent_e2e_seed_failed"` and a propagating exception.
4. Run:
   `make test-agent-e2e PYTEST_ARGS="tests/test_agent_e2e_seed.py -v"`.

## Validation

- [x] `agent_e2e_seed.md` documents failure-path test
- [x] `agent_e2e.md` module list mentions 862
- [x] Artifact `70-dev-docs.md` created
- [x] Roadmap STEP 8 marked complete
