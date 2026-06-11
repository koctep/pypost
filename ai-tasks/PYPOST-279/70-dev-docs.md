# PYPOST-279: Dev Docs

## Updates

| File | Change |
| --- | --- |
| `doc/dev/testing.md` | New **Pytest exit codes** section documenting exit `5` = failure policy |
| `doc/dev/testing.md` | Makefile automation table row for PYPOST-279 exit-code regression |

## Rationale

Developers and reviewers need a single reference for when `make test` or CI should fail on
collection errors, separate from test failures (exit `1`) or usage errors (exit `4`).
