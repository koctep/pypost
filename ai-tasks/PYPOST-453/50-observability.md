# PYPOST-453: Observability Implementation

## Logging Implementation

### Added Logs

**STEP 5 outcome:** No new log statements. PYPOST-453 codifies nested-call policy in
`FunctionExpressionResolver` without changing orchestration. `FunctionExpressionResolver`
remains log-free per PYPOST-452 architecture; nested valid and invalid placeholders flow
through existing `TemplateService` observability hooks.

**Existing logs (unchanged; apply equally to nested chains):**

- **WARNING**: `pypost/core/template_service.py` — `template_render_fallback_to_original`
  on validation or render fallback (`render_path`, `error_type`, `token_count`).
- **INFO**: `pypost/core/template_service.py` — `template_expression_validation_failed`
  when validation fails before render (`render_path`, `code`, `function_name`, `token_count`).
  Nested policy violations (e.g. unknown function inside a chain) emit the same structured
  fields with the **innermost offending** `function_name` from `ValidationResult`.
- **DEBUG**: `pypost/core/template_service.py` — `template_expression_render_succeeded`
  after successful render, including valid nested chains.

### Log Structure

- Structured logs: **yes** — fixed prefixes with `%s`/`%d` placeholders
- Includes context: **yes** — `render_path`, `code`, `function_name`, `token_count`
- Log levels: **INFO**, **WARNING**, **DEBUG**

## Metrics Implementation

**STEP 5 outcome:** No new counters or labels. Nested placeholders reuse existing
`MetricsManager` helpers on the `TemplateService` render path.

### Performance Metrics

- **Throughput**: `template_expression_render_attempts_total` — outcomes include
  `success`, `validation_error`, `render_error`, `empty_content` for nested and
  single-level expressions alike.
- **Error rate**: derivable from render attempts and
  `template_expression_validation_failures_total`.

### Business Metrics

- `template_expression_validation_failures_total` — records nested policy failures with
  the same `code` / `function_name` labels as top-level failures (e.g.
  `unknown_function` + `bad` for `{{md5(bad(db))}}`).
- `template_expression_render_attempts_total` — nested valid chains on `render_path=hover`
  record `outcome=success` identically to runtime.

### System Health Metrics

- Template expression render/validation counters in `pypost/core/metrics.py` (unchanged).

## Monitoring Integration

Integration with monitoring systems:

- [x] Prometheus metrics (existing counters)
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (ELK, Loki, etc.)

## Validation Results

Validation results:

- [x] Logs are correctly formatted (existing pipeline; nested paths verified by render
      tests)
- [x] Metrics are collected correctly for nested success and nested validation failure
- [x] Logging works in error scenarios (validation `ValueError` → WARNING fallback)
- [x] Large data structures are not logged (no template body or variables in logs)
- [x] Metrics are available for monitoring

### Tests added (STEP 5)

- `TestTemplateServiceObservability.test_render_nested_validation_failure_tracks_validation_metrics`
  — `{{md5(bad(db))}}` on `render_path=hover` → `validation_error` + `unknown_function` /
  `bad`; no `render_error`.
- `TestTemplateServiceObservability.test_render_nested_success_tracks_success_metric` —
  `{{md5(urlencode(db))}}` on `render_path=hover` → `outcome=success`.

Command:

- `./scripts/test.sh tests/test_template_service.py::TestTemplateServiceObservability -v`
  → all observability tests pass (including new nested cases).

## Notes

- Nested-call policy alignment does not widen the observability surface: resolver stays
  pure; orchestration owns logs and metrics.
- Requirements DoD parity (runtime vs hover) is covered by functional tests in STEP 3 and
  success-metric test on `hover` in STEP 5.
- Malformed nested edge observability parity is deferred to PYPOST-454.
