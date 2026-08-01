# PYPOST-959: Observability Implementation

## Summary

No new log events, metrics, or production instrumentation. Compound-key lookup
change is silent — same install log as PYPOST-868/902.

## Existing Events (unchanged)

| Event | Level | When | Token |
| --- | --- | --- | --- |
| `agent_e2e_http_stub_installed` | INFO | Stub CM `__enter__` | `name=url_router` for Mapping installs |

Logger: `pypost.fixtures.agent_e2e_http`.

## Test Coverage Added

| Test | Assert |
| --- | --- |
| `test_stub_agent_e2e_http_url_router_compound_key_mixed_case_method` | `get` / `PoSt` requests match `GET` / `POST` compound map keys |

## Checklist

- [x] No new production log volume
- [x] No per-route DEBUG on normalization
- [x] Unit proof primary evidence
