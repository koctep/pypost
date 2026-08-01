# PYPOST-963: Observability

## Failure signals

| Check | Signal on drift |
| --- | --- |
| `test_slow_smoke_seed_materializes_minimum_pypost_tree` | Assert message names expected vs actual `pypost/` files and points to policy constant |
| `test_slow_smoke_seed_includes_pyproject_packaging_artifacts` | Unchanged — missing pyproject-derived paths |
| Slow smoke (`make test-slow`) | Network install still fails if seed under-provisions metadata |

## Operator notes

- Fast contract tests run in default `make test` — no slow marker required.
- Policy constant name `SLOW_SMOKE_MINIMUM_PYPPOST_FILES` is grep-friendly for packaging PRs.

## Logging

N/A — contract tests use pytest assertions only.
