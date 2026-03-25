# PYPOST-84: Code Cleanup

## Summary

This task was a comment-only change to `tests/test_request_service.py`. No executable code
was modified, so no refactoring, dead-code removal, or style fixes were required.

## Changes Made

| File | Change |
|------|--------|
| `tests/test_request_service.py` | Added identical 3-line inline comment above each of the four `mock_executor.execute.return_value` assignments |

## Verification

```
make test
```

Result: **195 passed, 0 failures, 0 errors** — coverage threshold (50%) unaffected.

## Checklist

- [x] No trailing whitespace introduced
- [x] Line length ≤ 100 characters (comment lines are well within limit)
- [x] LF line endings preserved
- [x] No production code touched (AC-4)
- [x] All four patch sites annotated (AC-1, AC-2)
- [x] `make test` passes (AC-3)
