# PYPOST-794: Observability

## Scope

Makefile documentation change only — no runtime logging, metrics, or tracing affected.

## Verification

- `make help` — manual smoke: prints sorted target list with descriptions.
- `make check` — confirms lint and test suite still pass after Makefile edits.

## Notes

No observability gaps introduced. Help output goes to stdout; no log aggregation needed.
