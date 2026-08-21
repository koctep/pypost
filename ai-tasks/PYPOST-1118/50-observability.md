# Observability: PYPOST-1118

## Logging & Metrics

`env` expressions participate in the existing TemplateService observability framework:

1. **Metrics:**
   - `template_expression_render_attempts_total{render_path="...", outcome="success"}` increments on successful resolution of `env(...)`.
   - `template_expression_validation_failures_total{render_path="...", code="...", function_name="env"}` increments when invalid `env` expressions are evaluated (e.g. invalid arity `{{ env(a, b) }}`).

2. **Logging:**
   - Validation failures log an `INFO` message with `render_path`, `code`, `function_name="env"`, and token count.
   - Successful renders log a `DEBUG` message with `render_path` and token count.
   - Fallbacks log a `WARNING` message with `render_path`, `error_type`, and token count.

3. **Privacy & Security:**
   - Environment variable values and names are not logged in plain text during normal validation.
