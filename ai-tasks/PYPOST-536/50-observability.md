# PYPOST-536: Observability

## Impact

No new logs or metrics. Hover path still calls `TemplateService.render_string` with
`render_path="hover"`; only placeholder **detection** regex was unified.

## Existing coverage

| Signal | Path | Unchanged |
| --- | --- | --- |
| Hover render metrics | `VariableHoverHelper._resolve_expression_token` | Yes |
| Validation metrics | `FunctionExpressionResolver` via shared tokenizer | Yes |

## Verification

- Existing hover observability tests in `tests/test_variable_hover.py` pass.
- No changes to `MetricsManager` or log statements.
