# PYPOST-879: Observability Implementation

## Scope

**DOCUMENTATION / DECISION ONLY.** No production code and no harness helper
extraction. Timeout diagnostics remain as after PYPOST-828 / PYPOST-878.
Production logging, metrics, and monitoring integration are **N/A**.

## Observability Requirements Analysis

| Area | Assessment |
| --- | --- |
| Key production components | Unchanged |
| Critical path under test | Collection worker waits still use local detail |
| Production logging gap | None |
| Test harness diagnostics | Unchanged; defer shared worker helper |

Critical execution path (unchanged):

1. Collection worker tests wait via
   `process_until(..., timeout_detail=_worker_timeout_detail(worker))`.
2. On timeout: detail still includes `worker_running=…` via
   `format_storage_async_timeout_detail`.

## Logging Implementation

### Added Logs

No new production or harness syslog-style logging.

- **EMERG** / **ALERT** / **CRIT** / **ERR** / **WARNING** / **NOTICE** /
  **INFO** / **DEBUG**: N/A

### Log Structure

- Structured logs: N/A
- Includes context: N/A
- Log levels: none added

### Rationale (no production logging)

YAGNI deferral does not change how timeouts are reported in CI. Maintainers
still read pytest `AssertionError` text from `process_until`.

## Metrics Implementation (if applicable)

### Performance Metrics

None added.

### Business Metrics

None added.

### System Health Metrics

None added.

## Test-side diagnostics (unchanged channel)

| Helper | Status |
| --- | --- |
| `format_storage_async_timeout_detail` | Unchanged (used by local helper) |
| `gateway_timeout_detail` | Unchanged (multi-consumer gateway path) |
| Local `_worker_timeout_detail` | Kept in collection worker tests |
| Shared `worker_timeout_detail` | **Not added** (no second consumer) |

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics — N/A
- [ ] Grafana dashboards — N/A
- [ ] Alerting rules — N/A
- [ ] Log aggregation — N/A

## Validation Results

Validation results:
- [x] No new logs required
- [x] Existing timeout detail path unchanged
- [x] Large data structures not introduced into diagnostics
- [x] N/A for production monitoring

## Notes

If a second worker-only consumer appears later, extract a shared helper next to
`gateway_timeout_detail` and document it under Step 8 of that follow-up; do not
add production metrics for harness-only closures.
