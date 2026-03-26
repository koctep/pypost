# PYPOST-85: Tech Debt Review

## Summary

Replaced fragile private-attribute mutation in the reload test with `seed_collections()`.

## Change Quality

| Criterion | Verdict |
|-----------|---------|
| Correctness | PASS — scenario empty → seed → reload still validated |
| Scope | PASS — helpers + one test only |
| Coupling | PASS — tests use public fake API |

## Residual Tech Debt

**TD-1 (LOW, resolved):** `saved_collections` now stores full `Collection` objects (PYPOST-86,
  `8830703`).
