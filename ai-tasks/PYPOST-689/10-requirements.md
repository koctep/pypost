# PYPOST-689: Audit — performance and scalability

## Goals

PyPost is a desktop HTTP/MCP client where request latency, UI freeze windows, and memory growth
under large payloads directly affect operator experience. Template rendering, collection I/O, and
MCP inbound tool calls have received targeted optimizations (PYPOST-410, PYPOST-628, PYPOST-486),
but there is no consolidated audit of whether hot paths, threading model, and memory bounds form a
coherent scalability story.

This audit establishes an evidence-based picture of **performance and scalability** so the team
can prioritize gaps in response buffering, startup blocking, collection reload, and MCP
concurrency.

## Programming Language

Python (audit and analysis task; deliverables are markdown reports and follow-up items).

## User Stories

- As a **user sending requests**, I want the UI to stay responsive during network I/O and large
  response display, so I can cancel or navigate without multi-second freezes.
- As a **user with large collections**, I want startup and collection reload to scale without
  blocking the main thread for noticeable periods.
- As an **MCP operator**, I want inbound `call_tool` traffic to use background threads without
  starving the Qt event loop or serializing unrelated work unnecessarily.
- As a **maintainer**, I want a map of QThread vs daemon-thread boundaries and blocking I/O on
  the main thread, so new features follow existing async patterns.
- As a **tech-debt owner**, I want prioritized follow-ups (P1/P2/P3), so performance work is
  schedulable.

## Definition of Done

- [x] An audit report is stored under `ai-tasks/PYPOST-689/` with summary, scope, methodology,
  findings, and recommendations.
- [x] Findings cover request execution hot paths (`RequestWorker`, `RequestService`, `HTTPClient`).
- [x] Findings cover template rendering (`TemplateService`, compile cache, per-field renders).
- [x] Findings cover UI responsiveness (workers, debounce, main-thread blocking).
- [x] Findings cover MCP server threading (`MCPServerManager`, `run_in_threadpool`).
- [x] Findings cover large collection loading (`StorageManager`, `CollectionsPresenter`).
- [x] Findings cover memory patterns (response buffering, history cap, deep copies).
- [x] Findings cover blocking I/O on the main thread (startup, config, history load).
- [x] Each significant finding includes impact and a recommended remediation direction.
- [x] Findings are prioritized (P1/P2/P3) for follow-up ticketing.
- [x] Developer summary added at `doc/dev/performance_audit.md`.
- [x] Out-of-scope areas are explicitly listed.

## Task Description

**Problem:** Performance improvements landed incrementally without a single audit of end-to-end
latency, memory bounds, and main-thread blocking across GUI, HTTP, and MCP paths.

**Business intent:** Make scalability risks visible and schedulable — reducing surprise UI freezes,
runaway memory on large responses, and startup delays with many collections.

### In Scope

- `pypost/core/request_service.py`, `http_client.py`, `worker.py`
- `pypost/core/template_service.py`, `sensitive_data_masking_policy.py`
- `pypost/ui/presenters/` (tabs, collections, env), `response_view.py`, `main_window.py`
- `pypost/core/mcp_server.py`, `mcp_server_impl.py`
- `pypost/core/storage.py`, `request_manager.py`, `history_manager.py`
- `pypost/core/environment_storage_worker.py`, `environment_storage_gateway.py`
- Prior benchmark docs (PYPOST-455, PYPOST-410, PYPOST-486)

### Out of Scope

- Application code fixes (audit only).
- Load testing, flame graphs, or production APM traces.
- Network tuning (TCP, DNS, TLS session reuse beyond `requests.Session`).
- Database or server-side performance (client-only).
- Observability log volume (PYPOST-688).
- Security audit (cite PYPOST-685 only where memory exposure overlaps).

## Acceptance Criteria

| ID | Criterion |
| --- | --- |
| AC-1 | Report documents request execution thread model and hot-path render counts |
| AC-2 | Report documents template compile cache and sub-ms render baseline |
| AC-3 | Report documents UI worker inventory (QThread vs threading.Thread) |
| AC-4 | Report documents MCP `run_in_threadpool` bridge and uvicorn thread |
| AC-5 | Report documents collection load/reload blocking behavior |
| AC-6 | Report documents response body memory buffering and UI duplication |
| AC-7 | Report documents main-thread blocking I/O inventory |
| AC-8 | P1/P2/P3 follow-ups listed in `60-tech-debt.md` without Jira links |
