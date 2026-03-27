# PYPOST-422: Developer documentation — Retry exhaustion metric rename

## Overview

PYPOST-422 renames the Prometheus counter that records **outbound HTTP retry exhaustion**
so the series name matches behavior. The counter is **not** limited to email-specific
flows; it increments when **all configured retries** for a request are exhausted.

**Traceability:** [PYPOST-402](https://pypost.atlassian.net/browse/PYPOST-402) tech debt
**TD-5**, Jira **PYPOST-422**.

## Developer-facing changes

### Exported Prometheus series

| Aspect | Before (removed) | After (current) |
| ------ | ---------------- | ----------------- |
| Counter name | `email_notification_failures_total` | `request_retry_exhaustions_total` |
| Help text | (legacy) | `Outbound HTTP requests where all configured retries were exhausted` |
| Labels | `endpoint` | `endpoint` (unchanged semantics: request URL string) |

### Python API (`pypost/core/metrics.py`)

- **Registration:** Private field `_request_retry_exhaustions_total` holds the
  `prometheus_client.Counter`.
- **Public method:** `MetricsManager.track_request_retry_exhaustion(endpoint: str)` —
  replaces the former `track_email_notification_failure` name.
- **Call site:** `RequestService._emit_exhaustion_alert` in
  `pypost/core/request_service.py` (single increment path per exhaustion).

### Architecture choice

**Option A (hard rename):** The legacy series name is **not** exported alongside the
new one. Dashboards and alerts must be updated to query
`request_retry_exhaustions_total`; there is no deprecated alias counter in this
release.

## Migration notes (operators and integrators)

1. **Find usages** of `email_notification_failures_total` in Grafana, Prometheus
   alert rules, recording rules, and saved queries.
2. **Replace** the metric name with `request_retry_exhaustions_total`. Keep the
   `endpoint` label in selectors unless you intentionally aggregate across endpoints.
3. **Example PromQL migration:**

   ```promql
   # Before
   rate(email_notification_failures_total[5m])

   # After
   rate(request_retry_exhaustions_total[5m])
   ```

4. **Cardinality:** Unchanged — still one primary label `endpoint` (URL string).

## Tests and verification commands

### Focused pytest (metrics and retry behavior)

From the repository root, with the project virtualenv activated:

```bash
cd /home/src && . venv/bin/activate && \
  python3 -m pytest tests/test_metrics_manager.py tests/test_retry.py -q
```

**Expectation:** all tests pass (e.g. `42 passed` as recorded in STEP 5).

- `tests/test_metrics_manager.py` — scrapes the registry and asserts the text format
  line for `request_retry_exhaustions_total{endpoint=...}`.
- `tests/test_retry.py` — asserts `track_request_retry_exhaustion` on exhaustion
  paths and that it is not called when exhaustion does not occur.

### Static check for legacy names in application code

```bash
rg -n 'email_notification|track_email_notification' pypost/
```

**Expectation:** no matches in `pypost/` after PYPOST-422 (legacy identifiers removed
from the package).

## Observability implications

### What this metric measures

- **Increments when:** All retries for an outbound HTTP request are exhausted
  (exception path or retryable status path at `attempt == max_retries`).
- **Does not mean:** “email send failed” in isolation — correlate with logs and
  `request_errors_total` if needed.

### Related series (unchanged)

- `request_retries_total{method,status_category}` — per **retry attempt**, not
  exhaustion.
- `request_errors_total{category}` — errors surfaced from `execute`, including after
  exhaustion.

### Logs (troubleshooting)

- **WARNING** — logger `pypost.core.request_service`, prefix `retry_exhausted` in
  `_emit_exhaustion_alert`: structured fields include `method`, `url`, `request_name`,
  `retries`, `error_category`, etc. Emitted **before** the Prometheus increment.
- **ERROR** — `request_execution_failed` on execution failure (broader than the
  exhaustion-only signal).

If the counter moves but logs show no `retry_exhausted` for an incident, the issue may
not be retry exhaustion (check other paths and `request_errors_total`).

### Common pitfalls

| Symptom | Likely cause |
| ------- | ------------ |
| Query returns no data after upgrade | Dashboard still uses `email_notification_failures_total` |
| Spike in `request_errors_total`, flat exhaustion rate | Errors may be non-exhaustion paths |
| Duplicate-looking increments | Unlikely from rename: single call site; verify no custom forks |

## References

- Implementation: `pypost/core/metrics.py`, `pypost/core/request_service.py`
- STEP 5 detail: `ai-tasks/PYPOST-422/50-observability.md`
- Requirements: `ai-tasks/PYPOST-422/10-requirements.md`
