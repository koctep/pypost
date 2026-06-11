# PYPOST-340: Code Cleanup

## Review

- New helpers are private methods on `RequestManager`, matching existing `_rebuild_index`
  naming.
- Delete paths use explicit `del col.requests[i]` instead of list comprehension for
  clarity and early exit.
- Tests reuse `FakeStorageManager` and `unittest.mock.patch` patterns from the suite.

## Actions Taken

- None beyond implementation conventions.

## Remaining

- None.
