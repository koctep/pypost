# PYPOST-422: Observability Implementation

## Scope

STEP 5 verifies observability after the STEP 3 rename to
`request_retry_exhaustions_total` / `track_request_retry_exhaustion` (retry
exhaustion semantics). No additional logging or metrics were required; runtime
behavior was validated.

## Logging Implementation

### Logs Relevant to Retry Exhaustion

- **WARNING** — `pypost.core.request_service` — `_emit_exhaustion_alert`:
  message prefix `retry_exhausted` with `method`, `url`, `request_name`,
  `retries`, `error_category`, `error`, `detail`. Emitted **once** per HTTP
  exhaustion, **before** the Prometheus increment and optional alert emit.

- **ERROR** — `execute` — `request_execution_failed` after exhaustion (and other
  `ExecutionError` paths). This is the outcome log; it is **not** a duplicate
  exhaustion signal (distinct from `retry_exhausted`).

### Log Structure

- Structured key=value fields on the WARNING line; no large payloads.
- Log levels used: WARNING (`retry_exhausted`, retryable paths), ERROR
  (`request_execution_failed`).

## Metrics Implementation

### Business / HTTP Metrics

- **Metric:** `request_retry_exhaustions_total` (Counter).
- **Labels:** `endpoint` — request URL string (`request.url`); same meaning as before
  the rename.
- **When incremented:** all configured retries exhausted for an outbound HTTP
  request.
- **Code path:** `MetricsManager.track_request_retry_exhaustion` only; called from
  `_emit_exhaustion_alert` in `request_service.py`.

**Help text:** `Outbound HTTP requests where all configured retries were exhausted`
(`pypost/core/metrics.py`).

### Related Metrics (unchanged)

- `request_retries_total{method,status_category}` — per retry attempt (not
  exhaustion).
- `request_errors_total{category}` — incremented in `execute` when returning an
  `ExecutionResult` with error (including after exhaustion).

### Emission Points and Duplicates

- **Single call site:** `track_request_retry_exhaustion` is only invoked from
  `_emit_exhaustion_alert` (`request_service.py`).
- **Callers of `_emit_exhaustion_alert`:** (1) exception path when
  `attempt == max_retries`, (2) retryable status path when `attempt == max_retries`.
  Each path raises after `_emit_exhaustion_alert`, so **one** exhaustion increment
  per failed execution.
- **Rename verification:** `rg` over `pypost/` found **no** remaining
  `email_notification_failures_total` / `track_email_notification_failure`
  references (no duplicate legacy counter).

## Monitoring Integration

- [x] Prometheus counter exposed via existing `MetricsManager` registry / scrape
      (`tests/test_metrics_manager.py` asserts text format line for
      `request_retry_exhaustions_total{endpoint=...}`).
- [ ] Grafana dashboards (out of scope; ops-owned).
- [ ] Alerting rules (out of scope).
- [ ] Log aggregation (out of scope).

## Validation Results

- [x] `retry_exhausted` log aligns with the exhaustion counter (same function,
      log then metric).
- [x] Metric name and help match retry exhaustion (not email-specific).
- [x] Labels consistent (`endpoint` = URL).
- [x] No duplicate increments from rename (single method, single counter).
- [x] Tests: `42 passed` (see commands below).

## Verification Commands

```bash
cd /home/src && . venv/bin/activate && \
  python3 -m pytest tests/test_metrics_manager.py tests/test_retry.py -q
```

**Result (2026-03-27):** `42 passed`.

**Static checks:**

```bash
rg -n 'email_notification|track_email_notification' pypost/
```

**Result:** no matches (legacy names absent from application code).

## Notes

- Developer-facing docs under `doc/dev/` that still mention the old metric name
  are out of scope for STEP 5; FR-2 / AC-3 updates are tracked for STEP 7 per
  roadmap.
