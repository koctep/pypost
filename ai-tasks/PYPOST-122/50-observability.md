# PYPOST-122: Observability

## Assessment

This change is a performance optimization in the UI hover path. No new metrics, logs, or
tracing are required.

## Existing coverage

- Hover render path already records via `VariableHoverHelper` → `TemplateService` with
  `render_path="hover"` when function expressions are resolved.
- Line scoping does not alter which expressions are resolved or the render path.

## Decision

No additional observability instrumentation for this task.
