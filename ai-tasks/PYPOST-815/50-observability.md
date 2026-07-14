# PYPOST-815: Observability

N/A — configuration and annotation-only changes. No runtime logging, metrics, or tracing changes.

The mypy baseline gate remains the regression signal: `make typecheck` fails when new type errors
appear in `pypost/core/`, `pypost/models/`, or `pypost/ui/`.
