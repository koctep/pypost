# PYPOST-67: Code Cleanup

## Summary

Single-purpose change; no lint or format issues introduced.

## Checklist

| Item | Status |
|------|--------|
| Public method docstring on `reload_current_env` | Done |
| Removed external private call from `MainWindow` | Done |
| E2E test mocks updated to public API | Done |
| Line length ≤ 100 | Done |
| No unused imports | Done |

## Notes

- `_on_env_changed` remains private; in-class and unit-test call sites unchanged.
- `env_selector` property still exposed (TD-3 / PYPOST-68 — out of scope).
