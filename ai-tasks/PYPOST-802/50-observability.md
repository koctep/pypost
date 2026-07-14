# PYPOST-802: Observability

## Scope

Pure type refactor — no runtime logging, metrics, or tracing affected.

## Verification

- `make check` — lint and full test suite confirm no behavior change.

## Notes

No observability gaps introduced. History masking metrics and debug logs unchanged.
