# PYPOST-904: Observability Implementation

## Summary

Test-only observability lock: a marked `agent_e2e` GUI Send scenario now
asserts the existing HTTP stub install event under caplog on the live
offscreen path.

## Events Verified

| Event | Level | When | Module |
| --- | --- | --- | --- |
| `agent_e2e_http_stub_installed` | INFO | Stub CM enter during GUI Send | `pypost.fixtures.agent_e2e_http` |

Asserted token: `name=seed_get_ok` (matches `CANNED_SEED_GET_OK` on env Send).

## Coverage Layers

| Layer | Module | Path |
| --- | --- | --- |
| Unit matrix (PYPOST-870 / 903) | `tests/test_agent_e2e_http_stub_logs.py` | CM enter only |
| **GUI smoke (this ticket)** | `tests/test_agent_e2e_http_env.py` | Live session + Send |

## Caplog Contract

```python
with caplog.at_level(logging.INFO, logger="pypost.fixtures.agent_e2e_http"):
    with agent_e2e_http_stub(CANNED_SEED_GET_OK):
        session.ui_click(SEND_BUTTON)
        session.wait_for_snapshot(...)
assert "agent_e2e_http_stub_installed name=seed_get_ok" in caplog.text
```

## CI / Local

```bash
make test-agent-e2e PYTEST_ARGS="tests/test_agent_e2e_http_env.py::test_seeded_env_send_logs_http_stub_installed -v"
```

Grep fallback:

```bash
make test-agent-e2e PYTEST_ARGS="tests/test_agent_e2e_http_env.py -v" 2>&1 | grep agent_e2e_http_stub_installed
```

## Metrics

Not applicable. Developers grep install events in CI logs; catalog in
`doc/dev/logging.md`.

## Checklist

- [x] Install event asserted on GUI path (not unit-only)
- [x] Logger scoped caplog at INFO
- [x] No new production logs or metrics
- [x] Module timeout(60) + agent_e2e marker retained
