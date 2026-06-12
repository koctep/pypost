# PYPOST-148: Observability

## Current state

`TemplateService` already exports render and validation metrics (PYPOST-134, PYPOST-450):

- `template_expression_render_attempts{render_path, outcome}`
- `template_expression_validation_failures{render_path, code, function_name}`

## Decision impact

No new metrics. Deferral relies on existing counters as volume signals before adding compile
cache or render-duration histograms.

## Monitoring guidance

Use `template_expression_render_attempts` rate and user-reported hover lag as revisit triggers.
See `doc/dev/template_service.md` (PYPOST-148 closure) and
`doc/dev/template_expression_functions.md` (Caching evaluation).
