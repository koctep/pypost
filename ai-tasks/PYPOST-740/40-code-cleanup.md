# PYPOST-740: Code Cleanup

## Summary

Rename-only task; no logic changes.

## Checks

- [x] No stale `from pypost.core.request_sync` imports in `pypost/` or `tests/`.
- [x] `git mv` preserves history for module and test file.
- [x] flake8/analyze clean on touched Python files (via `make check`).

## Notes

Historical references in older `ai-tasks/` artifacts left unchanged (point-in-time records).
