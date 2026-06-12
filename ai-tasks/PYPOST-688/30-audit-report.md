# PYPOST-688: Observability and Logging Audit Report

**Task:** PYPOST-688 — Audit observability and logging
**Date:** 2026-06-12
**Scope:** Logging levels, structured context, MetricsManager/MetricsServer, MCP activity log,
alert webhooks, log_cli in tests/CI, sensitive data in logs
**Baseline:** PYPOST-685 security audit (E-003, M-004), PYPOST-686 test audit (log guardrails),
`doc/dev/testing.md`, `doc/dev/mcp_integration.md`
**Methodology:** ripgrep logger inventory, manual flow tracing per `20-architecture.md`, review of
metrics/alert/MCP modules, pytest.ini and CI workflow comparison. No code changes.

## Executive Summary

PyPost has a **mature but convention-driven** observability stack: **331 stdlib logger calls**
across **47 modules**, **31 Prometheus metrics** behind a `MetricsManager` facade, an in-memory
**MCP activity ring buffer** with count-only INFO events, and **AlertManager** writing JSON to a
rotating file plus optional HTTP webhooks. Test CI disables live `log_cli` but captures WARNING+
to `pytest.log` and enforces an ERROR allowlist (`baseline_error_count: 72`, margin 5).

**Three areas need immediate attention:**

1. **Resolved URLs in ERROR logs (P1)** — `http_client.py` logs fully rendered URLs on timeout,
   connection failure, and request errors; query params may contain API keys (PYPOST-685 E-003).
2. **`print()` bypasses logging (P1)** — five `print()` calls in `config_manager.py` and
   `style_manager.py` emit errors to stdout only; invisible to pytest log guardrails.
3. **No configurable log level (P2)** — `main.py` hardcodes `logging.basicConfig(level=INFO)`;
   operators cannot raise verbosity without code change.

Secondary findings: **key=value event naming** is consistent in newer modules but mixed with legacy
human-readable strings in `http_client`; **AlertManager** logs full `endpoint` at WARNING;
**metrics_registry._init_metrics** remains a 196-LOC monolith; local `log_cli=true` differs from
CI `log_cli=false`.

Findings use **P1** (credential exposure or guardrail bypass), **P2** (operational gap or
maintainability risk), **P3** (documented divergence or minor hygiene).

---

## Logging Inventory

### Scale (2026-06-12 grep)

| Metric | Value |
| --- | ---: |
| Modules with `logging.getLogger` | 47 |
| Total `logger.*` calls | 331 |
| `logger.info` | 124 |
| `logger.debug` | 108 |
| `logger.error` | 51 |
| `logger.warning` | 46 |
| `logger.exception` | 2 |
| `print()` in `pypost/` | 5 |
| f-strings in logger calls | 0 |

### Top modules by logger volume

| Module | Calls | Dominant level | Role |
| --- | ---: | --- | --- |
| `env_presenter.py` | 19 | info | Env/MCP UI orchestration |
| `tabs_presenter.py` | 20 | info | Tab send/save |
| `encryption_migration.py` | 24 | info/error | Migration progress |
| `request_service.py` | 16 | debug | Execution + retry |
| `request_manager.py` | 17 | warning | Collection I/O |
| `storage.py` | 14 | error | Persistence |
| `collection_tree_actions.py` | 14 | info/warning | Tree CRUD |
| `secret_store.py` | 13 | debug | Key backend lookups |

### Configuration (O-001)

```python
# pypost/main.py
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
```

**Assessment (P2):** Single root configuration at startup. No settings field for log level or
format. DEBUG logs (108 calls, including curl URLs and key-source paths) are **suppressed in
production** unless developers change code. Uvicorn threads for MCP/metrics servers use
`log_level="warning"` independently.

**Evidence:** `pypost/main.py` lines 14–17; `metrics_server.py` line 164; `mcp_server.py` equivalent.

---

## Structured Context

### Event naming convention (O-002 — PASS with gaps)

Newer modules use **snake_case event prefix + space-separated key=value** fields:

| Event | Module | Fields logged |
| --- | --- | --- |
| `mcp_activity_recorded` | `mcp_activity_log.py` | operation, outcome, tool_name, tool_count, mcp_arg_count, http_status, duration_ms |
| `alert_emitted` | `alert_manager.py` | request_name, endpoint, retries, error_category, webhook |
| `metrics_server_listening` | `metrics_server.py` | host, port |
| `metrics_server_start_failed` | `metrics_server.py` | host, port, message |
| `mcp_operation_start` | `mcp_client_service.py` | url, operation |
| `key_source_chain_active_attempt` | `key_sources/chain.py` | sources list |

**Legacy mixed format (P2):** `http_client.py` uses human-readable prefixes:

```text
Request timed out: GET https://api.example.com/v1?key=secret
Connection failed: POST https://...
```

No `extra={}` dict, structlog, or JSON application logs. Alert rotating file uses
`json.dumps(payload.to_dict())` on a dedicated logger — the only structured JSON log sink.

### print() bypass (O-003 — P1)

| File | Lines | Message |
| --- | --- | --- |
| `config_manager.py` | 29, 40, 51 | Config dir create / load / save errors |
| `style_manager.py` | 62, 65 | Style file read / directory scan errors |

These paths never reach pytest log capture or CI guardrails.

---

## Metrics Stack

### Architecture (O-004 — PASS)

```text
MetricsManager (facade, QObject)
├── MetricsRegistry — 31 Prometheus metrics, pure counters/histograms/gauge
└── MetricsServer — uvicorn thread, /metrics + MCP resources
```

`main.py` composition root: `MetricsManager()` → `start_server(settings.metrics_host,
settings.metrics_port)` → injected into `TemplateService`, `MainWindow`, workers.

### Metric inventory

| Type | Count | Examples |
| --- | ---: | --- |
| Counter | 28 | `requests_sent_total`, `gui_send_clicks_total`, `mcp_tool_call_duration_seconds` |
| Histogram | 1 | `mcp_tool_call_duration_seconds` |
| Gauge | 2 | `mcp_server_up`, (registry gauge for server state) |

**Total registrations:** 31 (`rg 'Counter\(|Histogram\(|Gauge\(' metrics_registry.py`).

**Assessment (P2):** `_init_metrics` spans **~196 LOC** in one method — hard to review when adding
metrics. Tracking methods on `MetricsManager` are thin delegates (good facade). Server lifecycle
logs (`Metrics server starting`, `metrics_server_listening`, `metrics_server_start_failed`) are
consistent with MCP server logs.

### MetricsServer logging

| Event | Level | Notes |
| --- | --- | --- |
| `Metrics server starting on %s:%d` | INFO | On thread start |
| `metrics_server_listening host=%s port=%d` | INFO | After uvicorn startup hook |
| `metrics_server_start_failed host=%s port=%d message=%s` | ERROR | Bind failures |
| `metrics_server_start_failed` | exception | Unexpected startup errors |
| `metrics_server_unexpected_exit` | WARNING | Thread died without stop |
| `Metrics server stopped` | INFO | Clean shutdown |

Uvicorn internal logs at WARNING only — reduces noise; application events carry bind diagnostics.

### Test coverage

**13 test modules** reference MetricsManager/MetricsServer/registry (`test_metrics_manager.py`,
`test_metrics_server_integration.py`, `test_history_masking_metrics.py`, etc.).

---

## MCP Activity Log

### Design (O-005 — PASS)

`McpActivityLog` — thread-safe ring buffer, default **100 entries**, optional `on_append`
callback for Qt signal refresh.

**Fields stored (UI + in-memory):** operation, outcome, tool_name, tool_count, mcp_arg_count,
http_status, detail, duration_ms. **No MCP argument values** (PYPOST-685 M-004 PASS).

**Application log on append (INFO):**

```python
logger.info(
    "mcp_activity_recorded operation=%s outcome=%s tool_name=%s tool_count=%s "
    "mcp_arg_count=%s http_status=%s duration_ms=%s",
    ...
)
```

**UI integration:** `EnvPresenter` opens `McpActivityDialog`; logs `mcp_activity_dialog_opened
entry_count=%d`.

**Gap (P2):** `detail` field may contain `execution_error.message` or `str(e)` from
`mcp_server_impl.py` — error text could echo upstream response fragments. Activity log is
in-memory only (not persisted), but INFO application log line omits `detail` (good).

**Tests:** `test_mcp_activity_log.py`, `test_env_presenter.py`, `test_env_persistence_e2e.py`.

---

## Alert Webhooks

### AlertManager (O-006 — PASS with P2 gap)

| Surface | Behavior |
| --- | --- |
| Rotating file | `{user_data_dir}/pypost-alerts.log`, 5 MB × 3 backups, JSON lines |
| Application logger | `alert_emitted` WARNING with request_name, **endpoint**, retries, category |
| Webhook | POST JSON via `requests`; 5 s timeout |
| Webhook success | DEBUG `alert_webhook_ok url=%r status=%d` |
| Webhook failure | WARNING `alert_webhook_failed url=%r error=%s` |
| Auth header | Sent in HTTP header; **never logged** (PASS) |

**Composition root:** `main.py` creates AlertManager from settings; `MainWindow` reloads on
settings change (`alert_manager_reloaded` INFO).

**Gap (P2):** `alert_emitted` and webhook debug/warning lines include **full endpoint URL** —
resolved URLs with query tokens appear in support logs. JSON file payload also includes full
`endpoint` (by design for operators; treat file as sensitive).

**Tests:** `test_alert_manager.py`, `test_main_window_alert_reload.py`,
`test_settings_alert_main_window_e2e.py`.

---

## Test and CI Logging

### Local vs CI (O-007)

| Setting | `pytest.ini` (local) | `.github/workflows/test.yml` (CI) |
| --- | --- | --- |
| `log_cli` | `true` | `false` (`-o log_cli=false`) |
| CLI level | `WARNING` | N/A (disabled) |
| File capture | — | `--log-file=pytest.log --log-file-level=WARNING` |
| Post-run | — | `verify_test_log_guardrails.py pytest.log` |

**Allowlist:** `tests/expected_log_allowlist.yaml` — `baseline_error_count: 72`, `error_margin: 5`.
Rules map logger name + message prefix (e.g. `pypost.core.http_client` / `Connection failed`).

**caplog tests:** **10 modules** use pytest `caplog` for asserting log content.

**Assessment (PASS):** CI guardrails prevent silent ERROR regression. **P3:** Local developers see
WARNING+ live during green runs; CI is quiet — documented in `doc/dev/testing.md` but easy to
miss when debugging CI-only failures.

---

## Sensitive Data in Logs

Cross-reference PYPOST-685. This audit focuses on **log-line exposure**.

| ID | Finding | Severity | Evidence |
| --- | --- | --- | --- |
| L-001 | Resolved URLs in http_client ERROR | **P1** | `http_client.py:240,247,254` — full rendered `url` |
| L-002 | Resolved URL in curl_generator DEBUG | P3 | `curl_generator.py:62,99` — DEBUG only |
| L-003 | Template URL in retry_policy DEBUG | P3 | `request_service.py:147` — template not resolved |
| L-004 | Alert endpoint in WARNING log | P2 | `alert_manager.py:109` — `endpoint=%r` |
| L-005 | Webhook URL in debug/warning | P2 | `alert_manager.py:131,133` — full webhook URL |
| L-006 | Key sources log key_id not values | PASS | `key_sources/*.py`, `environment_secrets_codec.py` |
| L-007 | MCP activity excludes arg values | PASS | `mcp_activity_log.py`; PYPOST-685 M-004 |
| L-008 | MCP safe_execution_log_fields counts | PASS | `mcp_server_impl.py` DEBUG counts only |
| L-009 | History observability masked URL | PASS* | `request_service.py` — masked when hidden_keys set |
| L-010 | print() config/style errors | **P1** | No logger; bypasses guardrails |

\* PASS with caveat from PYPOST-685 E-004: unmasked when `hidden_keys` empty.

---

## Findings Summary

| ID | Severity | Topic | Recommendation |
| --- | --- | --- | --- |
| L-001 | P1 | Resolved URLs in ERROR logs | Redact query params or log host+path only |
| L-010 | P1 | print() in config/style | Replace with `logger.error` |
| O-003 | P1 | Same as L-010 | — |
| O-001 | P2 | Hardcoded INFO log level | Settings or `PYPPOST_LOG_LEVEL` env |
| L-004 | P2 | Alert endpoint in logs | Log host + path or hash |
| L-005 | P2 | Webhook URL in logs | Log host only |
| O-004 | P2 | Monolithic _init_metrics | Split registration by domain |
| L-002 | P3 | curl DEBUG URLs | Acceptable at DEBUG; document |
| O-007 | P3 | Local vs CI log_cli | Already in testing.md; link from observability doc |

---

## Methodology Notes

Commands executed (2026-06-12):

```bash
rg -o 'logger\.(debug|info|warning|error|critical|exception)' pypost/ | sort | uniq -c
rg -l 'logging\.getLogger' pypost/ | wc -l
rg -c 'Counter\(|Histogram\(|Gauge\(' pypost/core/metrics_registry.py
rg -n 'print\(' pypost/
rg -l 'caplog' tests/ | wc -l
```

No application code modified. Line numbers reference commit at audit date.

## Related Tests

| Area | Test modules |
| --- | --- |
| Metrics | `test_metrics_manager.py`, `test_metrics_server_*.py`, `test_history_masking_metrics.py` |
| Alerts | `test_alert_manager.py`, `test_main_window_alert_reload.py` |
| MCP activity | `test_mcp_activity_log.py`, `test_env_presenter.py` |
| Log guardrails | CI runs `verify_test_log_guardrails.py` (not a pytest module) |

## Out of Scope

- OpenTelemetry / external APM
- Metrics cardinality under load
- Full PYPOST-685 secrets matrix re-audit
- Lint/complexity (PYPOST-687)
