# PYPOST-421: Observability Implementation

## Scope

HTTP retry exhaustion in `RequestService._execute_http_with_retry` and
`RequestService._emit_exhaustion_alert` (`pypost/core/request_service.py`), plus
Prometheus touchpoints in `MetricsManager` (`pypost/core/metrics.py`).

## Logging Implementation

### Existing signals (confirmed)

- **WARNING** — `retryable_error` / `retryable_status`: logged before back-off when
  another attempt will be made (not on final exhaustion).
- **WARNING** — `retry_exhausted`: emitted once per exhaustion via
  `_emit_exhaustion_alert` (method, url, request_name, retries, category, message).
- **ERROR** — `request_execution_failed`: `execute()` logs structured failure for any
  `ExecutionError` from HTTP execution (includes exhaustion); includes category and
  detail.
- **DEBUG** — `http_attempt`, `retry_backoff`, `retry_policy_resolved`, cancellation
  during back-off.

### Changes made (STEP 5)

- **WARNING** — `retry_exhausted`: added `detail=%s` (ExecutionError.detail) for
  correlation with `retries_attempted` and other structured detail without logging
  large payloads.
- **ERROR** — `retry_loop_invariant_failed`: logged only on the defensive path after
  the retry loop (should not run under normal `max_retries >= 0` control flow);
  supports investigation if the loop exits without return/raise.

### Log structure

- Structured key=value style on the module logger (`logging.getLogger(__name__)`).
- Context: method, url, attempt limits; exhaustion includes request_name and error
  fields.
- Levels used for this feature: DEBUG, WARNING, ERROR.

## Metrics Implementation

### Confirmed touchpoints

- **`request_retries_total`** (`track_retry_attempt`): per retry followed by back-off,
  after a retryable failure when `attempt < max_retries` (not on exhaustion).
- **`email_notification_failures_total`** (`track_email_notification_failure`): once
  per exhaustion inside `_emit_exhaustion_alert`.
- **`request_errors_total`** (`track_request_error`): once per `ExecutionError` in
  `execute()` (includes exhaustion).

### Duplicate emission analysis

- **No double `track_retry_attempt` on exhaustion**: exhaustion paths raise
  immediately after `_emit_exhaustion_alert`; the shared block that calls
  `track_retry_attempt` is not executed on the last attempt.
- **Single exhaustion funnel**: `_emit_exhaustion_alert` is the only place that
  increments `email_notification_failures_total` and emits `AlertPayload` for HTTP
  retry exhaustion.
- **`request_errors` vs `email_notification_failures`**: both increment on exhaustion
  by design (category-level errors vs exhaustion-specific counter); not duplicate
  emissions of the same metric.

### Monitoring integration

- [x] Prometheus metrics (existing counters in `MetricsManager`)
- [ ] Grafana dashboards (out of task scope)
- [ ] Alerting rules (out of task scope)
- [ ] Log aggregation (deployment-specific)

## Validation Results

- [x] Log lines for exhaustion include `retry_exhausted` with detail
- [x] Metrics: `track_email_notification_failure` once on exhaustion (tests)
- [x] No duplicate `track_retry_attempt` on final failure (control flow + tests)
- [x] `uv run --with pytest --with flake8 python -m flake8 pypost/core/request_service.py`
- [x] `uv run --with pytest python -m pytest tests/test_retry.py tests/test_request_service.py -q`
  — 55 passed

## Notes

- `request_execution_failed` (ERROR) after `retry_exhausted` (WARNING) is
  intentional: exhaustion is highlighted at WARNING with alert/metrics; `execute()`
  records the user-visible failure path once.
