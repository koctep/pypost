# PYPOST-450: Observability Implementation

## Logging Implementation

### Added Logs

Describe added logging:

- **EMERG**: not applicable for this desktop scope.
- **ALERT**: not applicable for this desktop scope.
- **CRIT**: not applicable for this desktop scope.
- **ERR**: not added in this slice; existing error logs unchanged.
- **WARNING**: `pypost/core/template_service.py` — `_fallback_content_after_render_exception`
  logs `template_render_fallback_to_original` with `render_path`, `error_type`, and
  `token_count` when validation or Jinja render fails and original content is returned.
- **NOTICE**: not used in current project logging setup.
- **INFO**: `pypost/core/template_service.py` — `_emit_validation_failure_observability`
  logs `template_expression_validation_failed` with `render_path`, validation `code`,
  `function_name` (or `n/a`), and `token_count`.
- **DEBUG**: `pypost/core/template_service.py` — `_emit_render_success_observability`
  logs `template_expression_render_succeeded` with `render_path` and `token_count`.

### Log Structure

Log format used:

- Structured logs: yes (key=value fields in message text)
- Includes context: yes (`render_path`, `code`, `function_name`, `token_count`, `error_type`)
- Log levels: `INFO`, `WARNING`, `DEBUG`

### Privacy / Data Boundaries

- No raw template strings, variable names, or variable payloads are logged.
- Only short contextual fields: path, outcome, validation code, function name, token count,
  exception type.

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics:

- **Response time**: not added for this ticket.
- **Throughput**: `template_expression_render_attempts_total` by `render_path`
  (`runtime` / `hover`) and `outcome` (`success` / `validation_error` / `render_error` /
  `empty_content`), defined in `pypost/core/metrics.py`, emitted from
  `pypost/core/template_service.py`.
- **Error rate**: derived from `template_expression_render_attempts_total{outcome!="success"}`
  and explicit `template_expression_validation_failures_total`.

### Business Metrics

Business metrics:

- `template_expression_validation_failures_total` tracks function-placeholder validation
  failures by `render_path`, `code`, and `function_name`, enabling visibility into
  unsupported or malformed function expressions in runtime and hover paths.

### System Health Metrics

System health metrics:

- No new host resource metrics in this scope (CPU/memory/disk unchanged).
- Component-level health proxy added via render/validation counters for `TemplateService`.

## Wiring and Module Split

Observability lives in `TemplateService` orchestration; validation logic is delegated to
`FunctionExpressionResolver` and execution to `FunctionRegistry` (no separate logging there).

| Path | Entry | Metrics wiring |
| --- | --- | --- |
| Runtime (HTTP send) | `HTTPClient._prepare_request_kwargs` → `render_string(..., render_path="runtime")` | `TemplateService(metrics=metrics_manager)` injected from `pypost/main.py` through `MainWindow` → `TabsPresenter` → `RequestWorker` → `HTTPClient` |
| Runtime (MCP/history) | `RequestService` → `render_string` | Same injected `TemplateService` instance |
| Hover preview | `VariableHoverHelper._resolve_expression_token` → `render_string(..., render_path="hover")` | `VariableHoverHelper.set_metrics(metrics)` called from `RequestWidget.__init__` in `pypost/ui/widgets/request_editor.py` |

Plain-variable hover (`{{var}}`) bypasses `TemplateService` and does not emit these
metrics — only function-style placeholders go through the observability pipeline.

## Monitoring Integration

Integration with monitoring systems:

- [x] Prometheus metrics (exposed via existing `MetricsManager` server on `/metrics`)
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (ELK, Loki, etc.)

## Validation Results

Validation results:

- [x] Logs are correctly formatted (key=value fields; verified in pytest live log output)
- [x] Metrics are collected correctly (`TestTemplateServiceObservability`, 8 tests)
- [x] Logging works in error scenarios (WARNING on fallback; INFO on validation failure)
- [x] Large data structures are not logged (no content/variable payloads in log fields)
- [x] Metrics are available for monitoring (Prometheus counters registered in `MetricsManager`)
- [x] Render-stage coverage (`TestTemplateServiceRenderStages`, 4 tests) — empty, validation
  failure, success, and Jinja render_error paths
- [x] Audit (2026-06-06): no observability gaps found vs architecture/requirements; no code
  changes required

Test run (STEP 5):

```text
.venv/bin/python -m pytest \
  tests/test_template_service.py::TestTemplateServiceObservability \
  tests/test_template_service.py::TestTemplateServiceRenderStages -q

12 passed, 2 subtests passed in 0.25s
```

HTTPClient integration tests (STEP 3) verify runtime rendering behavior for function
expressions in URL, headers, params, and body; observability is covered separately at the
`TemplateService` layer where both runtime and hover paths converge.

## Notes

- Scope intentionally limited to PYPOST-450 code paths: runtime render path and hover
  expression-render path.
- `render_path` label distinguishes runtime vs hover for dashboards and log filtering.
- Validation `ValueError` failures record `validation_error` (not `render_error`); only
  unexpected Jinja exceptions record `render_error`.
- Empty content short-circuits before validation and records `empty_content` outcome.
- Follow-up: orchestration density in `TemplateService` tracked in PYPOST-459; no additional
  observability work required for PYPOST-450 closure.
