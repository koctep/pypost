# Metric Rename Migration: Retry Exhaustion Counter

## Overview

[PYPOST-422](https://pypost.atlassian.net/browse/PYPOST-422) renamed the Prometheus counter
that records **outbound HTTP retry exhaustion** from `email_notification_failures_total` to
`request_retry_exhaustions_total`. The old name implied email-only failures; the new name
matches actual behavior (all configured retries exhausted for any outbound request).

[PYPOST-443](https://pypost.atlassian.net/browse/PYPOST-443) adds **transitional dual export**
and this operator migration guide so Grafana dashboards and Prometheus rules can be updated
without a monitoring gap.

| Aspect | Legacy (deprecated) | Canonical (current) |
| ------ | ------------------- | ------------------- |
| Counter name | `email_notification_failures_total` | `request_retry_exhaustions_total` |
| Labels | `endpoint` | `endpoint` (unchanged) |
| Status | Mirrored alias; scheduled for removal | Use for all new queries |

## Architecture

```mermaid
flowchart LR
  RS[RequestService._emit_exhaustion_alert]
  MM[MetricsManager.track_request_retry_exhaustion]
  CAN[request_retry_exhaustions_total]
  LEG[email_notification_failures_total deprecated alias]
  RS --> MM
  MM --> CAN
  MM --> LEG
```

- **Single increment path:** `track_request_retry_exhaustion(endpoint)` increments both series
  with the same `endpoint` label value.
- **Implementation:** `pypost/core/metrics.py` — see
  `_request_retry_exhaustions_total` and `_legacy_email_notification_failures_total`.
- **Call site:** `pypost/core/request_service.py` — unchanged from PYPOST-422.

## Rollout checklist (operators)

Use this checklist when deploying a build that includes PYPOST-422+ and PYPOST-443.

### 1. Discover legacy usage

Search Grafana, Prometheus alert rules, recording rules, and runbooks for:

```text
email_notification_failures_total
```

Tools: Grafana dashboard search, `rg` in config repos, Prometheus `query` API, or
`promtool check rules`.

### 2. Plan query updates

Replace the metric name; keep `endpoint` selectors unless aggregating across endpoints.

```promql
# Before
rate(email_notification_failures_total[5m])

# After (canonical)
rate(request_retry_exhaustions_total[5m])
```

During the transition window, both series receive identical increments — panels using either
name show the same data **after** PYPOST-443 is deployed.

### 3. Deploy and verify

1. Deploy the new PyPost build.
2. Scrape `/metrics/` (default port 9080) or MCP `metrics://all`.
3. Confirm both series appear:

   ```text
   request_retry_exhaustions_total{endpoint="..."}
   email_notification_failures_total{endpoint="..."}
   ```

4. Trigger or wait for a retry exhaustion event; verify both counters increment together.
5. Update dashboards and alerts to the canonical name.
6. Re-run verification on updated queries.

### 4. Communicate

- Notify dashboard and alert owners of the rename and sunset timeline.
- Link to this document in release notes or internal changelog.
- Record completion date when all production queries use the canonical name.

## Sunset timeline

The deprecated alias `email_notification_failures_total` is **temporary**. Target removal:
**next major release after all known consumers migrate**, or **6 months after PYPOST-443
ships**, whichever is later (operator confirmation required before removal).

After sunset, only `request_retry_exhaustions_total` is exported. Queries using the legacy
name return no data.

## Troubleshooting

| Symptom | Likely cause | Action |
| ------- | ------------ | ------ |
| No data for either metric | No retry exhaustions yet, or scrape target wrong | Check `/metrics/` endpoint and logs (`retry_exhausted` in `pypost.core.request_service`) |
| Legacy name works, canonical empty | Build predates PYPOST-422 | Upgrade to PYPOST-422+ |
| Canonical works, legacy empty | Build predates PYPOST-443 | Upgrade for alias window, or migrate queries to canonical |
| Both flat but errors spike | Non-exhaustion error path | Check `request_errors_total`; exhaustion is a subset |
| Duplicate concern | Two series, one event | Expected during transition; values should match per `endpoint` |

## Related documentation

- PYPOST-422 implementation notes: `ai-tasks/PYPOST-422/70-dev-docs.md`
- MCP and metrics testing: [testing.md](testing.md)
- Request execution and retries: [request_execution.md](request_execution.md)

## Tests

```bash
python3 -m pytest tests/test_metrics_manager.py tests/test_retry.py -q
```

Expect scrape output to include both `request_retry_exhaustions_total` and
`email_notification_failures_total` after `track_request_retry_exhaustion` is called.
