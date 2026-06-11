# PYPOST-443: Observability (STEP 5)

## Metrics contract

### Canonical

- **Name:** `request_retry_exhaustions_total`
- **Help:** Outbound HTTP requests where all configured retries were exhausted
- **Labels:** `endpoint`
- **Path:** `MetricsManager.track_request_retry_exhaustion` →
  `RequestService._emit_exhaustion_alert`

### Deprecated alias (transitional)

- **Name:** `email_notification_failures_total`
- **Help:** DEPRECATED — mirrors canonical counter; see `doc/dev/metric_rename_migration.md`
- **Labels:** `endpoint` (same value as canonical increment)
- **Behavior:** Incremented in the same call as canonical; no separate code path

## Cardinality

Unchanged — one `endpoint` label per series. Dual export doubles series count for this
metric family only during the sunset window.

## Verification

```bash
python3 -m pytest tests/test_metrics_manager.py::TestMetricsManagerRetryExhaustion -q
rg -n 'email_notification_failures_total|request_retry_exhaustions_total' pypost/core/
```

## Operator signals

- Migration guide: `doc/dev/metric_rename_migration.md`
- Logs unchanged: `retry_exhausted` WARNING in `request_service` before metric increment
