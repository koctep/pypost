# PYPOST-432: Observability — cov-fail-under raised to 60%

**Date**: 2026-06-11

## CI Summary

The GitHub Actions `Write job summary` step now reports `THRESHOLD=60`, matching `pytest.ini`.

When coverage meets threshold:

```
Required test coverage of 60% reached. Total coverage: 86.24%
```

## Local Verification

```bash
make test-cov
# TOTAL ... 86%
# Required test coverage of 60% reached.
```

Failure simulation:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ \
  --cov=pypost --cov-fail-under=99
# Exit code 2 — coverage below threshold
```

## Acceptance Criteria

| AC | Status |
|----|--------|
| AC-1 `pytest.ini` has `--cov-fail-under=60` | PASS |
| AC-2 `test.yml` `THRESHOLD=60` | PASS |
| AC-3 `make test-cov` exit 0 | PASS |
| AC-4 failure simulation non-zero | PASS |
