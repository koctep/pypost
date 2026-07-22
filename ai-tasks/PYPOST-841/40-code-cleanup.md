# PYPOST-841: Code Cleanup

## Actions

- Consolidated mid-start cleanup into one `except BaseException` path calling
  `shutdown()` (removed duplicate timeout-only shutdown call).
- Reset `_shut_down` at the start of a new `start()` attempt so retries after a
  failed start can still clean up.
- No drive-by refactors outside `lifecycle.py` / dedicated tests.

## Checklist

- [x] Idempotent shutdown still holds
- [x] Smoke + mid-start tests green
- [x] Typing and line length within project limits
