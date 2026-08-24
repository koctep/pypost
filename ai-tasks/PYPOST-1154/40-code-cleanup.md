# PYPOST-1154: Code Cleanup

## Scope

Makefile `WORKERS` default, always-on `--workers` flag, `default_worker_count()` in
`scripts/run_parallel_tests.py`, contract tests, and dev docs.

## Actions

- No formatting-only churn; changes follow existing Makefile and script style.
- `make lint` and `make typecheck` run in quality gate.

## Result

Pending `make check`.
