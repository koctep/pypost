# PYPOST-800: Observability

## Scope

Test-only change — no runtime logging, metrics, or tracing affected.

## Verification

- `make test` — new help smoke runs in fast suite.
- `make check` — lint + full fast test suite pass.

## Notes

Test failure message includes stderr when `make help` exits non-zero. Empty-output assertion
message states that `##` annotations may be missing.
