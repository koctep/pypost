# PYPOST-809: Observability

## Scope

Dev lock, Makefile, CI, and committed CSV — no runtime logging or metrics changes.

## Operational visibility

| Signal | Where |
| --- | --- |
| Inventory drift | `check-license-inventory` CI job log or `make check-license-inventory` stderr |
| Regeneration | `make generate-license-inventory` INFO log with output path |
| Tooling version | Pinned in `requirements-dev.txt` (`pip-licenses==5.5.5`) |
| Package count | 50 rows in `LICENSES/transitive.csv` (matches production lock) |

## CI job summary

The `check-license-inventory` job writes a GitHub Actions step summary documenting that
`LICENSES/transitive.csv` was verified against `requirements.txt` via pinned `pip-licenses`.

## N/A

- Application request/MCP/metrics logging — not affected by this task.
