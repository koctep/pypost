# PYPOST-132: Observability

## Assessment

Per-cell hover caching is a UI micro-optimization. No new metrics, logs, or tracing are
required.

## Existing coverage

- Hover render path already records via `VariableHoverResolver` → `TemplateService` with
  `render_path="hover"` when function expressions are resolved.
- Caching does not alter which expressions are resolved or the render path.

## Decision

No additional observability instrumentation for this task.
