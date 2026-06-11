# PYPOST-49: Split MetricsManager into MetricsRegistry and MetricsServer

## Goals

The PYPOST-40 SOLID audit (recommendation R7) identified that `MetricsManager` combined
Prometheus counter registration, observability MCP resource handlers, and uvicorn server
lifecycle in one module. That coupling made counter logic harder to unit-test in isolation and
violated single-responsibility expectations.

This task closes audit R7 by ensuring counters and server concerns are separated while
application wiring remains stable for presenters, workers, and services.

## Programming Language

Python (PySide6 / Qt), consistent with the PyPost desktop application.

## User Stories

- As a **developer**, I want counter definitions and `track_*` methods in a module with no
  network or threading code so I can test metrics without starting uvicorn.
- As a **developer**, I want MCP resource handlers and uvicorn lifecycle isolated so server
  changes do not risk counter registration logic.
- As a **maintainer**, I want existing `MetricsManager` injection sites to keep working without
  a sweeping type rename across the codebase.

## Definition of Done

- Prometheus counters and all `track_*` methods live in a dedicated registry component.
- MCP resource handlers and uvicorn `start` / `stop` / `restart` live in a dedicated server
  component.
- `MetricsManager` remains the composition-root facade passed through the app.
- Existing metrics unit tests pass (`test_metrics_manager`, `test_metrics_registry`,
  `test_metrics_server_endpoint`).
- No change to Prometheus metric names, labels, or scrape behavior.
- No change to MCP resource URI (`metrics://all`) or HTTP routes (`/metrics`, `/mcp`, `/sse`,
  `/messages`).
- Developer docs and PYPOST-40 tech-debt entry updated to reflect R7 resolution.

## Task Description

Follow-up from PYPOST-40 audit recommendation R7 (P2). Implementation was delivered in
[PYPOST-75](https://pypost.atlassian.net/browse/PYPOST-75) (PYPOST-44 TD-3). This sprint task
verifies acceptance criteria, completes workflow artifacts, and closes the audit tracker.

### In Scope

- Verify module split and facade delegation.
- Confirm tests and developer documentation.
- Mark R7 resolved in PYPOST-40 follow-up docs.

### Out of Scope

- `MetricsProtocol` / `NullMetrics` (PYPOST-44 TD-2).
- Injecting `MetricsRegistry` and `MetricsServer` separately at composition root.
- Changing metric names, labels, or observability routes.

### Constraints and Assumptions

- `main.py` constructs one `MetricsManager` and calls `start_server` before `MainWindow`.
- Call sites continue importing `MetricsManager` only.
- Counter-only tests may import `MetricsRegistry` directly.

## Functional Requirements

- `MetricsRegistry` owns `CollectorRegistry`, counter definitions, and all `track_*` methods.
- `MetricsServer` owns MCP `metrics://all`, Starlette app assembly, and uvicorn thread
  lifecycle; receives registry for scrape and MCP counter side effects.
- `MetricsManager` composes both and exposes the same public API as before the split.

## Non-functional Requirements

- **Testability:** registry module has no I/O imports from server module.
- **Compatibility:** no breaking changes for injected consumers.
- **Observability:** scrape output and MCP resource behavior unchanged.

## Main Entities and Interactions

| Entity | Role |
|--------|------|
| **MetricsRegistry** | Pure counter registry and tracking API (no I/O). |
| **MetricsServer** | Observability HTTP/MCP server and uvicorn lifecycle. |
| **MetricsManager** | Facade composed at `main.py`; delegates to registry and server. |
| **Application consumers** | Presenters, workers, services call facade `track_*` methods. |

## Q&A

| Question | Answer |
|----------|--------|
| Jira issue | [PYPOST-49](https://pypost.atlassian.net/browse/PYPOST-49) |
| Relation to PYPOST-75? | 75 implemented the split; 49 closes audit R7 with verification and docs. |
| Why keep `MetricsManager`? | Avoids renaming 20+ injection sites; facade is thin delegation. |
