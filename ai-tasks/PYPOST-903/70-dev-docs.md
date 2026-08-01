# PYPOST-903: Dev Docs (Step 8)

## Updated

| File | Change |
| --- | --- |
| `doc/dev/agent_e2e_http.md` | Caplog section lists parametrized matrix tokens (870/903); troubleshooting row cites 903 |

## Not changed

- `doc/dev/logging.md` — event catalog already documents `name=` variants
- `doc/dev/testing.md` — no new test tier or marker

## Author guidance summary

- Install caplog proofs live in `tests/test_agent_e2e_http_stub_logs.py`.
- Matrix covers all catalog constants plus `url_router` and one custom `name=`.
- Module must stay pure unit (no `agent_e2e` marker).

## Verification

Docs align with `_INSTALL_MATRIX` in
`tests/test_agent_e2e_http_stub_logs.py` and naming logic in
`pypost/fixtures/agent_e2e_http.py`.
