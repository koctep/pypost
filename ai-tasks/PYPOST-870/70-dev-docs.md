# PYPOST-870: Dev Docs Update

## Summary

Documented HTTP stub install-event caplog coverage (PYPOST-870) next to the
existing HTTP fixture / logging catalog docs. No new `doc/dev/` file was
required — `agent_e2e_http.md` and `logging.md` already described the event;
this step points at the automated proof.

## Changes

- `doc/dev/agent_e2e_http.md` — Stub install note + troubleshooting for
  install-log regressions; points at
  `tests/test_agent_e2e_http_stub_logs.py`
- `doc/dev/logging.md` — Catalog prose links the PYPOST-870 stub-logs
  caplog module

No user-facing docs (test-harness / developer observability only).
`doc/dev/logging.md` already catalogs `agent_e2e_http_stub_installed`
(PYPOST-859).

## Key developer guidance

1. Enter `stub_agent_e2e_http(CANNED_GOLDEN_OK)` (or any catalog result).
2. Assert under
   `caplog.at_level(logging.INFO, logger="pypost.fixtures.agent_e2e_http")`.
3. Expect `"agent_e2e_http_stub_installed name=golden_ok"` (or the matching
   catalog / custom / `url_router` token).
4. Run:
   `make test PYTEST_ARGS="tests/test_agent_e2e_http_stub_logs.py -v"`.

## Validation

- [x] `agent_e2e_http.md` documents install-log proof + troubleshooting
- [x] `logging.md` points at stub-logs tests
- [x] Artifact `70-dev-docs.md` created
- [x] Roadmap STEP 8 marked complete
