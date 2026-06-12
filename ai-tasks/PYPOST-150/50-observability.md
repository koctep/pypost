# PYPOST-150: Observability

## Logging

No new log statements. Existing `mcp_server_listening` and `metrics_server_listening` logs
remain the runtime signal for bind success.

## Tests

- Integration tests assert listen addresses via `lsof` when available; connection probe is
  the primary readiness check.

## Metrics

Not applicable — test-only change.
