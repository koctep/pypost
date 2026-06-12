# PYPOST-134: Observability

## Scope

Verification-only task. No observability changes required.

## Existing coverage (unchanged)

`TemplateService` already exports:

- `template_expression_render_attempt` counter (labels: `render_path`, `outcome`)
- `template_expression_validation_failure` counter
- Structured logs on validation failure and render fallback

Hover path uses `render_path="hover"` via `VariableHoverResolver._resolve_expression_token`.

## Result

No new logging or metrics. Centralization audit confirms observability remains on
`TemplateService` for all function-expression render paths.
