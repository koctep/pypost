# PYPOST-689: Observability (Audit Meta)

## Purpose

This audit is **read-only analysis** — no runtime instrumentation was added. This document records
how performance findings relate to existing observability (PYPOST-688) and what signals already
exist for performance regression detection.

## Existing Performance Signals

| Signal | Module | Use for performance |
| --- | --- | --- |
| `template_expression_render_attempt` counter | `TemplateService` | Volume by `render_path` and outcome |
| `template_compile_cache` DEBUG hits/misses | `TemplateService` | Compile LRU effectiveness |
| `request_complete` DEBUG elapsed_ms, size | `HTTPClient` | Per-response size and latency (worker log) |
| `history_manager_saved` DEBUG elapsed_ms | `HistoryManager` | Disk write duration |
| `refresh_tree_completed` INFO collection/request counts | `CollectionsPresenter` | Tree rebuild scale |
| `mcp_tool_call_duration_seconds` histogram | `MetricsManager` | Inbound MCP tool latency |

## Gaps Relevant to Performance

| Gap | Finding ref | Notes |
| --- | --- | --- |
| No response body size cap metric | P-003 | Size logged at DEBUG only after full download |
| No template render duration histogram | P-007 | Counters only; PYPOST-455 used local micro-bench |
| No main-thread block timing | P-013 | Startup collection load has no span/timer |
| No collection load duration metric | P-013, P-014 | Only post-hoc tree counts |

## Audit Execution Log

| Step | Action | Outcome |
| --- | --- | --- |
| Inventory | QThread vs threading.Thread grep | 4 + 3 modules |
| Hot path | Manual trace GUI → worker → HTTPClient | Documented in 30-audit-report |
| Benchmarks | Cross-ref PYPOST-455 tables | Sub-ms template; network dominates |
| Caps | grep DEFAULT_MAX_ENTRIES, LARGE_DOC | History 500, activity 100, UI 100 KB |

No pytest run required for audit deliverables. Related tests listed in `30-audit-report.md`.

## Relation to PYPOST-688

Observability audit covers log hygiene and metrics inventory. This audit uses DEBUG logs
(`request_complete`, `template_compile_cache`) as **secondary evidence** but does not re-audit
log levels or sensitive data in logs.
