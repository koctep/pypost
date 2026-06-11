# PYPOST-252: Dev Docs

## Updates

| File | Change |
| --- | --- |
| `doc/dev/testing.md` | Added "Core manager unit tests" section with module map and focused commands |

## Summary

Documented that pytest infrastructure (PYPOST-88, PYPOST-307, PYPOST-371) already satisfies the
original PYPOST-252 intent, and indexed the three test modules that cover `RequestManager` and
`StateManager` with `FakeStorageManager` and isolated config directory patterns.

## Verification

- Focused pytest commands in `doc/dev/testing.md` match actual test module paths.
- Test class names and scope table align with `tests/test_request_manager.py`,
  `tests/test_request_manager_delete.py`, and `TestStateManagerPersistence`.
