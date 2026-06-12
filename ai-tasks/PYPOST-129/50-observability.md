# PYPOST-129: Observability

## Existing metrics (unchanged)

| Signal | Location | Changed |
| --- | --- | --- |
| Hover render path | `VariableHoverResolver._resolve_expression_token` → `TemplateService` | No |
| Metrics injection | `VariableHoverResolver.set_metrics` (via `RequestWidget`) | Moved class only |

## Notes

- Refactor is structural; no new log lines or metrics required.
- `render_path="hover"` contract preserved.
