# PYPOST-958: Observability Implementation

## Summary

No new log events, metrics, or production instrumentation. This task adds a
GUI-path scenario that reuses existing Mapping install logging.

## Existing Events (unchanged)

| Event | Level | When | Token |
| --- | --- | --- | --- |
| `agent_e2e_http_stub_installed` | INFO | Stub CM `__enter__` | `name=url_router` for Mapping installs |

Logger: `pypost.fixtures.agent_e2e_http`.

## Test Coverage Added

| Test | Assert |
| --- | --- |
| `test_mapping_compound_keys_same_url_get_post_panel_outcomes` | Panel status + distinct GET/POST bodies after compound-key Sends |

Settle step names (diagnostics if timeout):

- `wait_response_after_mapping_compound_get_send`
- `wait_response_after_mapping_compound_post_send`

Prefix: `mapping compound-key Send settle failed`.

## Checklist

- [x] No new production log volume
- [x] Reuses existing `url_router` install on Mapping stub enter
- [x] Panel asserts primary proof (not caplog)
