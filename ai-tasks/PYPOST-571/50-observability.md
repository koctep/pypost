# PYPOST-571: Observability

## Scope

Proposal defines observability **guardrails for the test suite**, not production metrics.

## Guardrail observability

| Signal | Source | Consumer |
| --- | --- | --- |
| Unlisted ERROR during test run | `verify_test_log_guardrails.py` | CI job failure + stdout diff |
| ERROR/WARNING count vs baseline | Allowlist `global.max_*` | CI + local `make test` |
| Test duration / timeout ratio | `audit_test_durations.py` | GitHub Actions `::warning::` annotations |
| Allowlist drift | Quarterly inventory regen | Maintainer PR review |

## CI summary integration

Extend existing `.github/workflows/test.yml` job summary step (after junit/coverage) with:

- Unlisted ERROR count (0 = pass)
- Top 5 unlisted messages if any
- Tests with duration ratio >80% (when duration audit enabled)

## Production logging

No changes. Guardrails do not alter application log levels. Optional future work (deferred):
reduce ERROR-level logging on expected UI error paths — product decision per PYPOST-568.
