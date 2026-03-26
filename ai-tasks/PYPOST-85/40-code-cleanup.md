# PYPOST-85: Code Cleanup

## Summary

Small test-harness change: public `seed_collections` on `FakeStorageManager` and one test
update. No production code.

## Changes Made

| File | Change |
|------|--------|
| `tests/helpers.py` | Added `seed_collections` with docstring |
| `tests/test_request_manager.py` | Replaced `_collections` assignment with `seed_collections` |

## Verification

`make test` (or `pytest`) — full suite green.

## Checklist

- [x] No trailing whitespace; line length ≤ 100; LF endings
- [x] Tests do not touch `FakeStorageManager._collections` directly
