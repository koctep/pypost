# PYPOST-368: Observability

## Scope

Test-only ticket. No new logging or metrics in production code.

## Test Observability

- Integration tests run uvicorn at `log_level="warning"` to keep CI output quiet.
- Failures surface via pytest assertions and `TimeoutError` from `_wait_for_port` when the
  server fails to bind or listen.

## Existing Metrics (unchanged)

Live tool calls through an unmocked `RequestService` would increment `mcp_requests_received_total`
and `mcp_responses_sent_total`; integration tests mock execute and do not scrape Prometheus.
