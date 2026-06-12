# PYPOST-113: Observability

## Impact

No new logs or metrics. Hover still routes function tokens through
`TemplateService.render_string(render_path="hover")`; only plain-variable **detection**
was centralized.

## Existing coverage

| Signal | Path | Unchanged |
| --- | --- | --- |
| Hover render metrics | `VariableHoverHelper._resolve_expression_token` | Yes |
| Plain variable lookup | Direct env dict read in `_resolve_plain_variable` | Yes |

## Verification

- Existing `tests/test_variable_hover.py` suite passes unchanged.
- No changes to `MetricsManager` or log statements.
