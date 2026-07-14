# PYPOST-746 — Code Cleanup

## Lint / Format

- `make analyze` — clean after refactor
- No trailing whitespace or line-length violations introduced

## Structure

- Each helper has a one-line docstring describing its domain
- `_init_metrics` is a 4-line delegator

## Files Touched

| File | Change |
| --- | --- |
| `pypost/core/metrics_registry.py` | Split init into four helpers |
