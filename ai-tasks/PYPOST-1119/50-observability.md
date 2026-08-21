# Observability: PYPOST-1119

## Logging

- **Cycle Detection Warning**:
  When circular references between variables are detected (e.g. `a -> b -> a`), a warning log is emitted:
  `environment_variable_cycle_detected cycle=<path>`

- **Max Depth Warning**:
  When recursion exceeds the maximum chain limit (32 hops), a warning log is emitted:
  `environment_variable_max_depth_exceeded var=<name> depth=<depth>`

- **Resolution Error Warning**:
  If an unhandled exception occurs during evaluation of a variable expression, a warning log is emitted and the unrendered raw value is safely returned:
  `environment_variable_resolution_failed var=<name> error=<err>`

## Metrics

- Template rendering attempts and validation failures are recorded via existing `TemplateService` metrics tracking:
  - `template_expression_render_attempts_total{render_path="env_resolve", outcome="success"}`
  - `template_expression_render_attempts_total{render_path="env_resolve", outcome="validation_error"}`
  - `template_expression_render_duration_seconds{render_path="env_resolve"}`
