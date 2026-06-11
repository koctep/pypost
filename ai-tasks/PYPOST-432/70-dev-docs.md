# PYPOST-432: Developer Documentation

**Date**: 2026-06-11

## Changes

| File | Change |
|------|--------|
| `doc/dev/testing.md` | Added "Coverage threshold" section |
| `pytest.ini` | Threshold 50% → 60% |
| `.github/workflows/test.yml` | Summary `THRESHOLD` 50 → 60 |

## Coverage Threshold Policy

- Enforcement: `--cov-fail-under=60` in `pytest.ini` `addopts`
- CI summary: `THRESHOLD=60` in `.github/workflows/test.yml` (display only)
- Project target: 70% (follow-up PYPOST-565)
- Audit command: `make test-cov`

See `doc/dev/testing.md` for the canonical developer reference.
