# PYPOST-179: Observability (Step 5)

## Scope

No new metrics or application log statements. The generator is an offline maintainer script.

## Script logging

| Level | When |
| --- | --- |
| INFO | Successful write paths or `--check` pass |
| ERROR | `--check` failure (fixtures out of date) |

Logging uses stderr via `logging.basicConfig` — consistent with `scripts/encryption_migrate.py`.

## Operator guidance

Regenerate fixtures after changing `pypost/fixtures/mcp_test_fixtures.py`, then run
`scripts/generate_mcp_test_fixtures.py --check` in CI or locally before commit.
