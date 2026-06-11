# PYPOST-416 — Code Cleanup

## Summary

Test-only change. No production code modified.

## Checklist

- [x] No unused imports beyond `logging` for `assertLogs` level constant.
- [x] Test follows existing `test_worker_race.py` setup style.
- [x] No duplicate helpers introduced; setup inlined like sibling tests.
