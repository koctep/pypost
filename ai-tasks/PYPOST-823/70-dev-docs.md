# PYPOST-823: Dev Docs Update

## Summary

Documented the test-harness hang fix for encrypted-load responsiveness: hardened
`_process_until` with wall-clock deadline + cross-thread posted quit. No production
API docs required (test-only change).

## Changes

- `doc/dev/gui_testing.md` — new § Bounded nested `QEventLoop` waits (PYPOST-823);
  dual-deadline contract; hang-regression tests; hang troubleshooting row
- `doc/dev/testing.md` — GUI / Qt section pointer to wall-clock + posted-quit pattern
- `doc/dev/environment_storage_async.md` — Tests § hang defense for responsiveness harness

## Key developer guidance

1. Nested `QEventLoop.exec()` must return to Python on a wall-clock deadline.
2. QTimer-only timeouts are insufficient; SIGALRM does not interrupt stuck C++ `exec()`.
3. Post `loop.quit()` via daemon `threading.Timer` → `QTimer.singleShot(0, loop, loop.quit)`.
4. Keep signal-method `pytest.mark.timeout`; do not use `method="thread"` for Qt waits.
5. Prefer shared `qapp`; reference `_process_until` in
   `tests/test_env_storage_responsiveness.py`.

Sibling gateway/worker `_process_until` copies remain on the old pattern — [PYPOST-827].

## Validation

- [x] Docs match hardened `_process_until` and hang-regression tests
- [x] Cross-links between testing / GUI / async env storage docs
- [x] Roadmap STEP 7 marked complete
