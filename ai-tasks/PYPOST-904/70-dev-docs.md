# PYPOST-904: Dev Docs Update

## Summary

Documented GUI-path HTTP stub install-log caplog smoke (PYPOST-904) alongside
the existing PYPOST-870 / 903 pure-unit matrix proofs.

## Changes

- `doc/dev/agent_e2e_http.md` — Env Send module note + troubleshooting row for
  GUI-path install caplog smoke

## Key developer guidance

1. **Fast unit matrix (no Qt):**
   `make test PYTEST_ARGS="tests/test_agent_e2e_http_stub_logs.py -v"`
   (PYPOST-870 / 903)
2. **Live e2e smoke (offscreen Qt):**
   `make test-agent-e2e PYTEST_ARGS="tests/test_agent_e2e_http_env.py::test_seeded_env_send_logs_http_stub_installed -v"`
3. Assert under
   `caplog.at_level(logging.INFO, logger="pypost.fixtures.agent_e2e_http")`
   with stub context wrapping Send click.

## Validation

- [x] `agent_e2e_http.md` notes GUI-path install caplog smoke
- [x] Troubleshooting distinguishes unit matrix vs GUI smoke
- [x] Roadmap STEP 8 marked complete
