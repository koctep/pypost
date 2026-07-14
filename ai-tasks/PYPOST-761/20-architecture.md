# PYPOST-761 — Architecture

## Approach

Add a second histogram alongside `mcp_tool_call_duration_seconds` in the HTTP metrics domain
(template counters already live in `_init_http_metrics`).

## Data flow

```text
TemplateService.render_string
  → render_with_jinja (template_service_render.py)
      perf_counter start
      compile_template + template.render
      finally → metrics.track_template_expression_render_duration(render_path, seconds)
```

Duration is recorded only when Jinja runs (post-validation). Empty content and validation
failures do not emit histogram samples.

## Touch points

| Module | Change |
| --- | --- |
| `metrics_registry.py` | Histogram + `track_template_expression_render_duration` |
| `metrics_protocol.py` | Protocol method + `NullMetrics` no-op |
| `metrics_otel.py` | OTel histogram mirror |
| `qt/metrics.py` | Facade delegate |
| `template_service_render.py` | Timing in `render_with_jinja` |
| `template_service.py` | Pass metrics + `render_path` to helper |

## Tests

- `tests/test_metrics_registry.py` — Prometheus scrape count line
- `tests/test_metrics_manager.py` — facade scrape
- `tests/test_metrics_otel.py` — OTel histogram count
- `tests/test_template_service.py` — success path + helper unit tests

## Inventory impact

Prometheus instrument count: 32 → 33 (second histogram).
