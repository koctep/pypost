# PYPOST-457: Observability

## Summary

No observability changes. This task adds acceptance tests only.

## Existing Coverage

Template expression metrics and logging are unchanged:

- `TemplateService.render_string` still records validation/render outcomes via
  `MetricsManager` when configured.
- Parity tests do not invoke metrics paths; they assert registry ↔ globals binding only.

## Gap Analysis

No new log lines, metrics, or tracing required for a test-only debt item.

## Validation

- [x] Confirmed no production code paths modified
- [x] No new hot-path instrumentation needed
