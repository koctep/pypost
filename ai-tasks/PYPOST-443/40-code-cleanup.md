# PYPOST-443: Code Cleanup (STEP 4)

## Scope

- `pypost/core/metrics.py` — alias counter registration and mirror increment
- `tests/test_metrics_manager.py` — dual-export assertion
- `doc/dev/metric_rename_migration.md` — new operator guide
- `doc/dev/README.md` — index link

## Lint / format

- No new flake8 issues in touched Python files (minimal diff, follows existing `Counter` style).
- Help string wrapped to stay within project line-length conventions.

## Tests

```bash
python3 -m pytest tests/test_metrics_manager.py tests/test_retry.py -q
```

**Result:** all tests pass (run at commit time).

## Notes

- Full-repo `make lint` may still report pre-existing issues outside this task scope
  (unchanged from PYPOST-422).
