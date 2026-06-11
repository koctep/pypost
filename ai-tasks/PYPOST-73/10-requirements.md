# PYPOST-73: Metrics tracker protocol for consumers

## Goals

After PYPOST-44 removed the `MetricsManager` singleton, all consumers still depend on the
concrete `MetricsManager` class for type hints. That coupling prevents alternative
implementations (no-op tracker, OpenTelemetry adapter, focused test doubles) without
changing call sites again.

This task introduces a structural protocol for the `track_*` surface so consumers depend
on an abstraction, not the full facade that also owns uvicorn and MCP lifecycle.

## User Stories

- As a **developer**, I want services and presenters to accept a metrics tracker protocol so
  I can inject fakes without importing `MetricsManager`.
- As a **maintainer**, I want the composition root (`main.py`, `MainWindow`) to remain the
  only place that needs server lifecycle APIs on the concrete facade.
- As a **test author**, I want `MagicMock(spec=MetricsTrackerProtocol)` to satisfy type
  checkers and runtime protocol checks.

## Definition of Done

- [x] `MetricsTrackerProtocol` defines all `track_*` / `set_mcp_server_up` methods used by
  consumers.
- [x] `MetricsManager` satisfies the protocol (structural subtyping + runtime check).
- [x] Key consumers type-hint `MetricsTrackerProtocol | None` instead of `MetricsManager`.
- [x] Composition root keeps `MetricsManager` where server lifecycle is required.
- [x] Tests pass; protocol satisfaction covered by unit test.

## Task Description

Source: PYPOST-44 technical-debt item TD-1 in `ai-tasks/PYPOST-44/60-review.md`.

**In scope:** Protocol definition, consumer type hints, protocol unit test.

**Out of scope:** `NullMetrics` no-op implementation (PYPOST-44 TD-2); splitting
`MetricsManager` (PYPOST-75, done); changing Prometheus metric names.

## Q&A

| Question | Answer |
| --- | --- |
| Why not rename `MetricsManager`? | Facade still owns server/MCP; only tracking consumers switch to protocol. |
| Is behavior changing? | No — type-level refactor only. |
