# PYPOST-97: Observability

## Scope

Documentation-only task. No new logs, metrics, or tracing.

---

## Decision

No observability changes required. `JsonHighlighter` remains a synchronous UI paint-path
helper; documenting regex limitations does not affect runtime instrumentation.
