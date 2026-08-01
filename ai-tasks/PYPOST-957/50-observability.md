# PYPOST-957: Observability Implementation

## Summary

No new log events, metrics, or production instrumentation. This task adds a
GUI-path caplog proof for an **existing** install log.

## Existing Events (unchanged)

| Event | Level | When | Token |
| --- | --- | --- | --- |
| `agent_e2e_http_stub_installed` | INFO | Stub CM `__enter__` | `name=url_router` for Mapping installs |

Logger: `pypost.fixtures.agent_e2e_http`.

## Test Coverage Added

| Test | Assert |
| --- | --- |
| `test_mapping_send_logs_http_stub_installed_url_router` | `agent_e2e_http_stub_installed name=url_router` under caplog during live Mapping GUI GET Send |

## Coverage Matrix (install log)

| Path | Module | Token |
| --- | --- | --- |
| Pure unit matrix | `tests/test_agent_e2e_http_stub_logs.py` | All catalog + `url_router` + custom |
| GUI single-canned | `tests/test_agent_e2e_http_env.py` | `seed_get_ok` (904) |
| GUI Mapping | `tests/test_agent_e2e_http_mapping_multi_url.py` | `url_router` (957) |

## Checklist

- [x] Logging works for Mapping install on GUI path (re-assert only)
- [x] No new production log volume
- [x] Caplog scoped to fixture logger at INFO
