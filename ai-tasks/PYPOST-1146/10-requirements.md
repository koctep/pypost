# PYPOST-1146: Metrics: Modularize MetricsManager to eliminate dynamic getattr delegation

## Goals

PyPost operators and maintainers rely on accurate, discoverable metrics instrumentation for
WebSocket sessions and the broader GUI. The current `MetricsManager` Qt facade uses dynamic
attribute delegation to stay within a strict file size guard, which hides tracking methods from
IDE autocompletion and static analysis. This task improves maintainability and developer
experience without changing observable metric behavior.

## User Stories

- As a **PyPost maintainer**, I want `MetricsManager` to declare its tracking methods explicitly
  so that I can navigate and refactor metrics calls with IDE support and type checkers.
- As a **contributor adding WebSocket metrics**, I want a clear, modular place to add delegation
  methods so that the 185-line LOC guard on `metrics.py` is not bypassed with `__getattr__`.
- As an **operator**, I want Prometheus scrape output and metric labels to remain unchanged so
  that existing dashboards and alerts keep working.

## Definition of Done

- `MetricsManager` no longer uses `__getattr__` to forward calls to `MetricsRegistry`.
- All nine WebSocket tracking/setter methods are explicitly defined on `MetricsManager` (or its
  documented mixin modules) with type hints.
- `pypost/core/qt/metrics.py` stays within the SOLID audit LOC cap.
- Existing metrics integration tests pass; no change to counter names, labels, or values.
- Developer documentation reflects the modular delegation pattern.

## Task Description

PYPOST-1136 introduced WebSocket session metrics via dynamic delegation in
`pypost/core/qt/metrics.py` to avoid exceeding the 185-line cap. PYPOST-1146 resolves that
technical debt by splitting tracking delegation into focused mixin modules while preserving the
Qt-facing `MetricsManager` public API.

## Q&A

| Question | Answer |
| --- | --- |
| Why not raise the LOC cap instead? | The cap prevents unbounded growth of the facade; modular extraction is the intended pattern (see PYPOST-1136 follow-up). |
| Will presenters need code changes? | No — public method names and signatures stay the same. |
| Does this change runtime metric behavior? | No — delegation still forwards to the same `MetricsRegistry` instance. |
