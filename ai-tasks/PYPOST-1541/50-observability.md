# PYPOST-1541: Observability

## Scope

Test-harness only (no production MCP listen path changes). Logging is for
diagnosing residual bind flakes under parallel `make test`.

## Logging Added

| Location | Level | Event / fields |
| --- | --- | --- |
| `tests/helpers/mcp_live_server.py` `LiveMCPServer.start` | WARNING | `mcp_live_server_bind_retry attempt=%d port=%d error=%s` on listen readiness timeout before retry |
| `tests/helpers/mcp_live_server.py` `LiveMCPServer.start` | INFO | `mcp_live_server_bind_retry_succeeded attempt=%d port=%d` when a retry attempt becomes ready |

No large payloads or credentials are logged (port integers and exception text only).

## Metrics

N/A — test helper; no Prometheus/OTel counters added for suite-only retries.

## Validation

- Forced first-reservation steal in
  `test_live_mcp_server_starts_when_allocated_port_stolen_before_listen` exercises
  the retry path (attempt ≥ 2).
- Successful first-bind path stays quiet at INFO/WARNING (no retry logs).

## Checklist

- [x] Structured context on retry (attempt, port, error)
- [x] No sensitive data in logs
- [x] N/A production metrics for this debt fix
