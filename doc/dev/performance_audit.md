# Performance and Scalability Audit

This document summarizes the PyPost performance and scalability audit (PYPOST-689). It complements
[request_execution.md](request_execution.md) (pipeline), [template_service.md](template_service.md)
(compile cache), [environment_storage_async.md](environment_storage_async.md) (async I/O precedent),
and [observability_audit.md](observability_audit.md) (metrics/logs).

## Audit Report

Full report:
[ai-tasks/PYPOST-689/30-audit-report.md](../../ai-tasks/PYPOST-689/30-audit-report.md)

**Date:** 2026-06-12 | **Scope:** Hot paths, threading, memory, main-thread I/O

## Executive Summary

| Metric | Value |
| --- | --- |
| `QThread` worker modules | 4 |
| Daemon `threading.Thread` modules | 3 |
| `render_string` references | 28 |
| Template render (typical HTTP) | ~0.7 ms (PYPOST-455) |
| History cap | 500 entries |
| Large-doc UI threshold | 100 KB |
| MCP activity cap | 100 entries |

PyPost offloads **network sends** and **encrypted environment I/O** to background workers.
Template rendering is **sub-millisecond** with a compile LRU. Gaps: **unbounded HTTP response
buffering**, **synchronous collection load at startup**, and **JSON pretty-print on the main
thread** for large bodies.

## Thread Model

PyPost uses **Qt main thread** for all widgets and **QThread** / **daemon threads** for I/O and
network work. See the full inventory and remediation status in
[performance_audit.md](performance_audit.md#thread-model).

```text
Main thread (Qt)
├── CollectionsPresenter / ResponseView / TabsPresenter
├── Startup: async collection load (CollectionStorageWorker) + env load gate
├── Streaming: chunk buffer flushed every ~33 ms (TabsPresenter)
└── StateManager debounced config save

QThread workers
├── RequestWorker              → RequestService.execute
├── CollectionStorageWorker    → startup / reload collection JSON (PYPOST-754/757)
├── EnvironmentStorageWorker   → encrypted env load/save (PYPOST-486)
├── EncryptionMigrationWorker
└── PasteJsonFormatWorker

Daemon / pool threads
├── MCPServerManager → uvicorn; call_tool limited by asyncio.Semaphore (PYPOST-759)
├── MetricsServer    → /metrics scrape
├── HistoryManager   → debounced history.json save
└── HistoryManager   → deferred startup history.json load (PYPOST-762)
```

## Request Hot Path

```text
TabsPresenter → RequestWorker → RequestService.execute
  → HTTPClient.send_request (stream=True, iter_content, full body join)
  → ScriptExecutor (post-script, same worker)
  → HistoryManager.append (async save)
```

- URL rendered **once** per send (PYPOST-410).
- Headers/params: **2× render_string** per key and value.
- **No max response size** — entire body held in RAM before UI display (P1).

## Template Rendering

- One shared `jinja2.Environment` per injected `TemplateService`.
- `@lru_cache(maxsize=256)` on template compile (PYPOST-628).
- DEBUG logs: `template_compile_cache hits/misses`.
- Prometheus histogram `template_expression_render_duration_seconds` labeled by `render_path`
  (`runtime`, `hover`, `curl`) — PYPOST-761.

## UI Responsiveness

| Protection | Threshold |
| --- | --- |
| Response search debounce | 100 KB doc, 250 ms |
| Match count cap | 1000 on large docs |
| Paste JSON format worker | 100 KB |
| State save debounce | 300 ms |

| Risk | Severity |
| --- | --- |
| `display_response` JSON pretty-print | P2 — no size guard |
| Streaming `append_body` per chunk | P2 — event-loop flood on fast SSE |
| `refresh_tree` full rebuild | P2 — on collection reload |

## MCP Threading

Inbound `call_tool` runs on uvicorn's asyncio loop and delegates sync work to
`run_in_threadpool(RequestService.execute)`. MCP server and metrics server use **daemon threads**
independent of Qt. Default threadpool size is **not configured** (P2).

## Collection and History I/O

| Operation | Thread | Notes |
| --- | --- | --- |
| `load_collections` at startup | Main | Sequential `json.load` per file (P1) |
| `save_collection` | Caller | Full `model_dump_json` rewrite |
| `HistoryManager._load` at startup | Daemon (async) | Deferred via `defer_initial_load`; panel refreshes when ready (PYPOST-762) |
| `HistoryManager` save | Daemon | Debounced async write |

Incremental tree insert exists for single saves; full reload rebuilds the model.

## Memory Bounds

| Surface | Bound |
| --- | --- |
| HTTP response body | **None (P1)** |
| History | 500 entries |
| MCP activity | 100 entries |
| Tab copies | `model_copy(deep=True)` per isolated tab |

## Follow-up Work

Twelve items in [60-tech-debt.md](../../ai-tasks/PYPOST-689/60-tech-debt.md) — P1: 2, P2: 6,
P3: 4. Prioritize response size cap and async collection load.

## Related Commands

```bash
# Worker inventory
rg -l 'QThread|threading\.Thread' pypost/

# Render call sites
rg -c 'render_string' pypost/

# Large-doc constants
rg 'LARGE_DOC|100 \* 1024|DEFAULT_MAX_ENTRIES' pypost/
```
