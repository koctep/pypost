# PYPOST-688: Audit — observability and logging

## Goals

PyPost ships Prometheus metrics, MCP activity logging, alert webhooks, and stdlib application
logging across **47 modules** with **331 logger calls**, but there is no consolidated audit of
whether logging levels, structured context, metrics wiring, and test/CI log guardrails form a
coherent observability story.

This audit establishes an evidence-based picture of **observability and logging** so the team can
prioritize gaps in log hygiene, metrics maintainability, and sensitive-data exposure in logs.

## Programming Language

Python (audit and analysis task; deliverables are markdown reports and follow-up items).

## User Stories

- As a **maintainer**, I want a consolidated inventory of logging levels and event naming, so new
  code follows existing key=value conventions.
- As an **operator**, I want clarity on MetricsManager, MetricsServer, alert webhooks, and MCP
  activity log behavior, so production troubleshooting is predictable.
- As a **CI operator**, I want confirmation that `log_cli`, `--log-file`, and
  `verify_test_log_guardrails.py` work together, so unexpected ERROR logs fail merges.
- As a **security reviewer**, I want sensitive-data-in-logs findings cross-referenced with
  PYPOST-685, so remediation does not duplicate security audit work.
- As a **tech-debt owner**, I want prioritized follow-ups (P1/P2/P3), so observability work is
  schedulable.

## Definition of Done

- [x] An audit report is stored under `ai-tasks/PYPOST-688/` with summary, scope, methodology,
  findings, and recommendations.
- [x] Findings cover logging levels and configuration (`basicConfig`, module loggers, DEBUG/INFO
  split).
- [x] Findings cover structured context (event naming, key=value fields, JSON alert file).
- [x] Findings cover MetricsManager, MetricsRegistry, and MetricsServer lifecycle and metrics
  inventory.
- [x] Findings cover MCP activity log (ring buffer, INFO events, UI integration).
- [x] Findings cover AlertManager (rotating JSON log, webhook delivery, log lines).
- [x] Findings cover `log_cli` in `pytest.ini`, CI overrides, and guardrail scripts.
- [x] Findings cover sensitive data in logs (URLs, endpoints, keys, cross-ref PYPOST-685).
- [x] Each significant finding includes impact and a recommended remediation direction.
- [x] Findings are prioritized (P1/P2/P3) for follow-up ticketing.
- [x] Developer summary added at `doc/dev/observability_audit.md`.
- [x] Out-of-scope areas are explicitly listed.

## Task Description

**Problem:** Observability features grew organically (Prometheus counters, MCP activity UI, alert
webhooks, CI log allowlists) without a single audit of consistency, gaps, and sensitive-data
exposure in application logs.

**Business intent:** Make logging and metrics behavior visible and schedulable — reducing surprise
ERROR noise, log bundles with credentials, and opaque metrics registration.

### In Scope

- `pypost/` application logging (`logging.getLogger`, levels, formats).
- `pypost/core/metrics.py`, `metrics_registry.py`, `metrics_server.py`.
- `pypost/core/mcp_activity_log.py`, MCP server activity recording.
- `pypost/core/alert_manager.py`, alert webhook settings UI.
- `pytest.ini`, `.github/workflows/test.yml`, `scripts/verify_test_log_guardrails.py`.
- Sensitive data in logs (URLs, endpoints, tokens) — cross-reference PYPOST-685.

### Out of Scope

- Application code fixes (audit only).
- OpenTelemetry, external log aggregation, or Datadog integration.
- Runtime profiling or metrics cardinality analysis under load.
- Security audit re-run (cite PYPOST-685; do not duplicate full secrets matrix).
- Lint/complexity audit (PYPOST-687).

## Acceptance Criteria

| ID | Criterion |
| --- | --- |
| AC-1 | Report documents logger call counts by level and top modules |
| AC-2 | Report documents metrics stack (facade, registry, server) and counter inventory |
| AC-3 | Report documents MCP activity log fields and application log events |
| AC-4 | Report documents AlertManager file + webhook paths |
| AC-5 | Report documents local vs CI pytest logging configuration |
| AC-6 | Report documents sensitive-data log findings with PYPOST-685 cross-ref |
| AC-7 | P1/P2/P3 follow-ups listed in `60-tech-debt.md` without Jira links |
