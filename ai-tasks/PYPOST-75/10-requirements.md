# PYPOST-75: Split MetricsManager responsibilities

## Goals

`MetricsManager` combined Prometheus counter tracking, observability MCP resource exposure,
and uvicorn server lifecycle in one class. That coupling made the module harder to test in
isolation and violated single-responsibility expectations from the PYPOST-40 SOLID audit
(PYPOST-44 TD-3, follow-up PYPOST-49).

This task separates those concerns so developers can reason about counters independently
from HTTP/MCP server startup, while keeping existing application wiring stable.

## User Stories

- As a **developer**, I want counter definitions and `track_*` methods in a pure module with
  no network or threading code so I can unit-test metrics without starting a server.
- As a **developer**, I want uvicorn lifecycle and MCP resource handlers isolated so server
  changes do not risk counter registration logic.
- As a **maintainer**, I want existing `MetricsManager` injection sites to keep working
  without a broad refactor of presenters, workers, and services.

## Definition of Done

- [x] Prometheus counters and all `track_*` methods live in a dedicated registry component.
- [x] MCP resource handlers and uvicorn `start` / `stop` / `restart` live in a dedicated
  server component.
- [x] `MetricsManager` remains the composition-root type passed through the app (facade).
- [x] All existing `tests/test_metrics_manager.py` tests pass unchanged.
- [x] No change to Prometheus metric names, labels, or scrape behavior.
- [x] No change to MCP resource URI (`metrics://all`) or HTTP routes (`/metrics`, `/mcp`,
  `/sse`, `/messages`).

## Task Description

Source: PYPOST-44 technical-debt item TD-3 ([PYPOST-76](https://pypost.atlassian.net/browse/PYPOST-76)),
planned as PYPOST-49 in the SOLID audit.

**In scope:** Internal module split; facade for backward compatibility.

**Out of scope:** `MetricsProtocol` / `NullMetrics` (PYPOST-44 TD-2); live uvicorn integration
tests; changing composition root to inject `MetricsRegistry` and `MetricsServer` separately.

## Q&A

| Question | Answer |
| --- | --- |
| Why keep `MetricsManager`? | PYPOST-44 already injected it across 20+ modules; facade avoids a sweeping type rename. |
| Is behavior changing? | No — structural refactor only. |
| Parent debt ticket? | [PYPOST-44](https://pypost.atlassian.net/browse/PYPOST-44) TD-3 |
