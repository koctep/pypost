# PYPOST-688: Observability Implementation

**Task type:** Audit only — no application code changes.

## Logging Implementation

### Application logging assessment

PyPost uses **stdlib `logging`** with module-level loggers. Audit inventory:

| Signal | Value |
| --- | ---: |
| Modules with loggers | 47 |
| Total logger calls | 331 |
| INFO / DEBUG / ERROR / WARNING | 124 / 108 / 51 / 46 |
| Root config | `basicConfig(level=INFO)` in `main.py` |
| Structured JSON (app) | AlertManager rotating file only |
| print() bypass | 5 (config_manager, style_manager) |

**Assessment:** Logging coverage is **broad** across core I/O, presenters, and server lifecycle.
Convention-driven key=value events in newer code; legacy string formats in `http_client`.

### User-visible vs log-only errors

| Layer | Mechanism |
| --- | --- |
| HTTP errors | Logged in `http_client` + surfaced via ExecutionError to UI |
| Alert exhaustion | `AlertManager.emit` → file + webhook + WARNING log |
| MCP bind failure | `start_failed` signal → status bar message |
| Config errors | **print() only** — gap |

## Metrics Implementation

| Component | Role | Log events |
| --- | --- | --- |
| `MetricsManager` | Facade + Qt signal for bind failures | Delegates to server |
| `MetricsRegistry` | 31 Prometheus instruments | None (pure counters) |
| `MetricsServer` | uvicorn thread, /metrics, MCP resources | start/listen/fail/stop |

**Assessment (PASS):** Metrics and logs complement each other — counters for aggregates, logs for
bind failures and lifecycle. No metric exposes PII; labels use method/status/source enums.

## MCP Activity Log

| Event | Level | Sensitive fields |
| --- | --- | --- |
| `mcp_activity_recorded` | INFO | Counts only; no arg values |
| `mcp_activity_cleared` | INFO | count |
| `mcp_activity_dialog_opened` | INFO | entry_count |

**Assessment (PASS):** Aligns with PYPOST-141 and PYPOST-685 M-004.

## Alert Webhooks

| Event | Level | Notes |
| --- | --- | --- |
| `alert_manager_init` | DEBUG | log_path, webhook yes/no |
| `alert_emitted` | WARNING | Includes endpoint — P2 gap |
| `alert_webhook_ok` | DEBUG | Full webhook URL |
| `alert_webhook_failed` | WARNING | Full webhook URL + error |

JSON alert file is the authoritative structured record; application logs are operational echoes.

## Test Log Observability

| ID | Severity | Finding |
| --- | --- | --- |
| O-001 | PASS | CI captures WARNING+ to pytest.log |
| O-002 | PASS | ERROR allowlist with baseline 72 + margin 5 |
| O-003 | P1 | print() errors bypass log capture |
| O-004 | P2 | Local log_cli=true shows more WARNING noise than CI |
| O-005 | PASS | 10 caplog tests assert log content |

## Validation Results

- [x] Logging inventory documented
- [x] Metrics stack documented
- [x] MCP activity and alert paths documented
- [x] CI guardrails documented
- [x] Gaps noted for Step 6 follow-ups

## Follow-up

See `60-tech-debt.md` — twelve remediation items (P1: 2, P2: 6, P3: 4).
