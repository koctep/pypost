# PYPOST-813: Observability

N/A — annotation-only change. No runtime logging, metrics, or tracing changes.

The mypy baseline gate remains the regression signal: `make typecheck` fails when new type
errors appear in scoped modules.
