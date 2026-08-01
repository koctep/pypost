# PYPOST-965: Observability

Refactor-only task — no runtime logging or metrics.

## Test signals (unchanged)

| Test | Signal |
| --- | --- |
| `test_slow_smoke_seed_includes_pyproject_packaging_artifacts` | Shared helper produces all pyproject-derived paths |
| `test_slow_smoke_seed_materializes_minimum_pypost_tree` | Shared helper yields policy stub tree |
| `TestSlowInstallSmoke` (via fixture) | End-to-end `make install` in assembled workspace |

## Drift prevention

Contract tests now call `_materialize_slow_smoke_workspace` — the same function the
`make_workspace_full_deps` fixture uses — so assembly drift fails in fast `make test`.
