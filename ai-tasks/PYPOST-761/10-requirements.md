# PYPOST-761 — Requirements

> Parent: [PYPOST-689](https://pypost.atlassian.net/browse/PYPOST-689) audit R-P3-001 / P-007

## Problem

Template rendering has attempt counters (`template_expression_render_attempts_total`) but no
latency histogram. PYPOST-455 relied on ad-hoc micro-benchmarks for render timing.

## User Stories

- As an **operator**, I want a Prometheus histogram of Jinja render duration by path, so I can
  detect regressions and size alerts.
- As a **maintainer**, I want duration tracking on the existing metrics protocol surface, so
  Prometheus and OTel backends stay aligned.

## Acceptance Criteria

1. Register `template_expression_render_duration_seconds` histogram labeled by `render_path`
   (`runtime`, `hover`, and existing `curl` callers).
2. Wire `track_template_expression_render_duration` through `metrics_registry`,
   `metrics_protocol`, `qt/metrics.py`, and `metrics_otel.py`.
3. Time Jinja compile+render in `template_service_render.render_with_jinja`.
4. Unit tests assert scrape/OTel histogram samples and render helper duration calls.
5. Update `doc/dev/performance_audit.md` and `doc/prometheus_monitoring.md`.
6. `make check` passes.

## Out of Scope

- Changing histogram bucket definitions (Prometheus client defaults)
- Recording duration for empty content or validation-only paths (no Jinja work)
- High-cardinality guards beyond existing `render_path` label set
