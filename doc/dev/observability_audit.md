# Observability and Logging Audit

This document summarizes the PyPost observability and logging audit (PYPOST-688). It complements
[security_audit.md](security_audit.md) (sensitive data in logs), [testing.md](testing.md) (pytest
log_cli and CI guardrails), and [mcp_integration.md](mcp_integration.md) (MCP activity viewer).

## Audit Report

Full report:
[ai-tasks/PYPOST-688/30-audit-report.md](../../ai-tasks/PYPOST-688/30-audit-report.md)

**Date:** 2026-06-12 | **Scope:** Logging, metrics, MCP activity, alerts, test/CI logs

## Executive Summary

| Metric | Value |
| --- | --- |
| Modules with loggers | 47 |
| Total `logger.*` calls | 331 |
| INFO / DEBUG / ERROR / WARNING | 124 / 108 / 51 / 46 |
| Prometheus instruments | 31 |
| `print()` in `pypost/` | 5 |
| caplog test modules | 10 |
| CI ERROR allowlist baseline | 72 (+ margin 5) |

PyPost uses stdlib logging with a **key=value event convention** in newer modules, a
**MetricsManager** facade over Prometheus + uvicorn, an in-memory **MCP activity log** (counts
only), and **AlertManager** JSON files plus optional webhooks. CI disables live `log_cli` but
verifies captured logs against an allowlist.

**Top gaps:** resolved URLs in `http_client` ERROR logs (P1), `print()` in config/style paths
(P1), hardcoded INFO log level (P2).

## Logging Configuration

```python
# pypost/main.py — root config at startup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
```

There is no settings-driven log level today. DEBUG logs (curl URLs, key-source lookups) are
suppressed unless developers change this configuration.

### Event naming

Preferred pattern (newer code):

```text
mcp_activity_recorded operation=call_tool outcome=success tool_name=foo mcp_arg_count=2 ...
metrics_server_listening host=127.0.0.1 port=9080
alert_emitted request_name='Get User' endpoint='https://...' retries=3 error_category=network
```

Legacy pattern (migrate when touching):

```text
Connection failed: GET https://api.example.com/v1?key=secret
```

## Metrics Stack

```text
MetricsManager
├── MetricsRegistry — 31 Counter/Histogram/Gauge (no I/O)
└── MetricsServer — uvicorn thread: /metrics + MCP metrics resources
```

Lifecycle logs: `Metrics server starting`, `metrics_server_listening`, `metrics_server_start_failed`,
`Metrics server stopped`. Uvicorn internal logs at WARNING.

```bash
# Local metrics tests
pytest tests/test_metrics_manager.py tests/test_metrics_server_integration.py -v
```

## MCP Activity Log

- **Buffer:** 100 entries, thread-safe ring buffer (`McpActivityLog`)
- **Stored fields:** operation, outcome, tool_name, counts, http_status, duration_ms — **no arg
  values**
- **App log:** INFO `mcp_activity_recorded` with key=value fields
- **UI:** Top-bar **MCP Activity (N)** → `McpActivityDialog`

See [mcp_integration.md](mcp_integration.md) for operator workflow.

## Alert Webhooks

| Surface | Location / behavior |
| --- | --- |
| JSON log file | `{user_data_dir}/pypost-alerts.log` (5 MB × 3 rotations) |
| Webhook | POST JSON from settings; auth header never logged |
| App log | WARNING `alert_emitted` (includes endpoint — treat as sensitive) |

Reload on settings save via `MainWindow._reload_alert_manager`.

## Test and CI Logging

| Setting | Local (`pytest.ini`) | CI (`test.yml`) |
| --- | --- | --- |
| `log_cli` | `true` | `false` |
| Level | `WARNING` | file: `WARNING` |
| Guardrail | — | `verify_test_log_guardrails.py pytest.log` |

See [testing.md — Pytest live logging (log_cli)](testing.md#pytest-live-logging-log_cli-pypost-570)
for local vs CI rationale.

## Sensitive Data in Logs

| Area | Status | Notes |
| --- | --- | --- |
| http_client ERROR URLs | **P1 gap** | Full resolved URL including query params |
| MCP activity | PASS | Counts only |
| Key sources | PASS | key_id logged, not key material |
| Alert endpoint in WARNING | P2 | Full URL in log line |
| config/style errors | **P1** | `print()` only |

Details and cross-reference to PYPOST-685: [30-audit-report.md](../../ai-tasks/PYPOST-688/30-audit-report.md).

## Follow-up Work

Twelve items in [60-tech-debt.md](../../ai-tasks/PYPOST-688/60-tech-debt.md) — P1: 2, P2: 6, P3: 4.
Prioritize URL redaction and print→logger migration.

## Related Commands

```bash
# Logger inventory (approximate)
rg -o 'logger\.(debug|info|warning|error)' pypost/ | sort | uniq -c

# CI log guardrail (after pytest with --log-file)
python scripts/verify_test_log_guardrails.py pytest.log

# Metrics registration count
rg -c 'Counter\(|Histogram\(|Gauge\(' pypost/core/metrics_registry.py
```
