# PYPOST-761 — Observability

## New metric

| Name | Type | Labels | Emitted when |
| --- | --- | --- | --- |
| `template_expression_render_duration_seconds` | Histogram | `render_path` | Jinja compile+render completes (success or render exception) |

## Existing signals unchanged

- `template_expression_render_attempts_total` — outcome counters still drive success/error rates
- DEBUG `template_compile_cache` — compile LRU stats
- DEBUG `template_expression_render_succeeded` — success log with token count

## Operator queries

```promql
histogram_quantile(0.99, sum(rate(template_expression_render_duration_seconds_bucket[5m])) by (le, render_path))
```

## Tests

- `tests/test_metrics_registry.py::TestMetricsRegistryTemplateRenderDuration`
- `tests/test_metrics_manager.py::test_track_template_expression_render_duration`
- `tests/test_metrics_otel.py::test_track_template_expression_render_duration_records_histogram`
- `tests/test_template_service.py` — integration + helper duration assertions
