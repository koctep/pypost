# PYPOST-750 — Requirements

> Parent: [PYPOST-688](https://pypost.atlassian.net/browse/PYPOST-688) audit R-P3-002

## Problem

PyPost registers Prometheus instruments in `pypost/core/metrics_registry.py`, but operators
lack a single catalog listing every metric name, type, labels, and meaning. The user-facing
`doc/prometheus_monitoring.md` summarizes a few HTTP and MCP counters and incorrectly states
that only counters are registered.

## User Stories

- As an **operator**, I want a complete metrics table, so I can build dashboards and alerts
  without reading Python source.
- As a **maintainer**, I want the catalog sourced from `metrics_registry.py`, so documentation
  stays aligned with registrations.

## Acceptance Criteria

1. `doc/prometheus_monitoring.md` lists every Prometheus instrument from `metrics_registry.py`
   with name, type (Counter/Gauge/Histogram), labels, and operator-facing meaning.
2. Inventory grouped by domain (GUI, HTTP, MCP, encryption).
3. Correct instrument-type summary (counters, one gauge, one histogram).
4. No application code changes.
5. `make check` passes.

## Out of Scope

- Adding new metrics or changing registry behavior
- OpenTelemetry export mapping (`metrics_otel.py`)
- Automated doc generation from source
