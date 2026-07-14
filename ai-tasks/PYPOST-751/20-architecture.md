# PYPOST-751: Architecture

## Scope

Single module change: `pypost/core/http_client.py` — three `logger.error` calls in
`send_request` exception handlers.

## Event mapping

| Legacy prefix | New event | Fields |
| --- | --- | --- |
| `Request timed out:` | `http_request_timed_out` | `method`, `url` |
| `Connection failed:` | `http_connection_failed` | `method`, `url` |
| `Request failed:` | `http_request_failed` | `method`, `url`, `detail` |

URLs use `%r` and `_error_log_url(url, variables)` — unchanged from PYPOST-741.

## Test impact

- `tests/test_http_client.py` — assert event name in `TestHTTPClientErrorLogging`
- `tests/expected_log_allowlist.yaml` — replace legacy prefixes with new event names

No behavioral change to `ExecutionError` categories or raised messages.
