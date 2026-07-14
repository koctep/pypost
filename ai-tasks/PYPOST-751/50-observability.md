# PYPOST-751: Observability

## Logging changes

Three `HTTPClient` ERROR paths now emit structured key=value events:

| Event | Level | Fields |
| --- | --- | --- |
| `http_request_timed_out` | ERROR | `method`, `url` (sanitized) |
| `http_connection_failed` | ERROR | `method`, `url` (sanitized) |
| `http_request_failed` | ERROR | `method`, `url` (sanitized), `detail` |

## CI guardrails

`tests/expected_log_allowlist.yaml` updated — legacy `Connection failed` / `Request timed out` /
`Request failed` prefixes removed.

## Metrics

No new metrics.
