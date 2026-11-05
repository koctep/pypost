# PYPOST-1425: Technical Debt Analysis

## Shortcuts Taken

1. **Cooperative checkpoints for local filesystem I/O**:
   `LibraryManagerService` checks `cancellation_token` between steps rather than
   interrupting mid-`read()` syscalls. True mid-read abort applies when a transport
   layer registers a close callback (socket/session). Local disk reads that never
   register a callback still finish their current syscall before the next check.
2. **Duck-typed token injection via `call_with_cancellation_token`**:
   Workers pass `cancellation_token` when the callable accepts it, and fall back
   without the keyword for legacy doubles. This preserves older test mocks but means
   services that ignore the keyword silently skip transport abort until updated.
3. **Generation discard retained**:
   Dialog generation counters remain as a secondary safety net; abort is primary.

## Code Quality Issues

1. `get_connection()` still calls `list_connections()` without forwarding an outer
   cancellation token, so nested listing during `list_manifest_collections` /
   `read_collection` may do a short uncancellable store load before the next check.
2. Dialog close still uses fixed `wait(1000)` joins; could adopt
   `adaptive_thread_join` from PYPOST-1437 for consistency (out of scope here).

## Missing Tests

1. Integration test with a real `requests`/`httpx` session registering
   `session.close` on the token (fault-injection network abort) — deferred to
   broader flaky-network suite (related PYPOST-1426).
2. Stress: rapid open/cancel/close of the import dialog while abort callbacks close
   live sockets under load.

## Performance Concerns

1. Cooperative checks add negligible overhead per manifest collection entry.
2. Disposing token sources per worker run is O(callbacks); expected callback count
   is small (one transport close).

## Follow-up Tasks

1. **Forward cancellation tokens through nested library lookups**:
   - Suggested SP: 2
   - Thread `cancellation_token` through `get_connection` / nested `list_connections`
     so store loads during fetch/discovery honor the same abort signal.
   - Jira: [PYPOST-1452](https://pypost.atlassian.net/browse/PYPOST-1452)
2. **Adaptive join on dialog worker teardown**:
   - Suggested SP: 2
   - Replace fixed `wait(1000)` in import-dialog cancel/close with
     `adaptive_thread_join` for faster teardown when abort succeeds.
   - Jira: [PYPOST-1453](https://pypost.atlassian.net/browse/PYPOST-1453)
3. **HTTP session abort registration for remote library transports**:
   - Suggested SP: 3
   - When library I/O gains a real HTTP client path, register `session.close` /
     socket shutdown on the worker token (pairs with PYPOST-1426 fault injection).
   - Jira: [PYPOST-1454](https://pypost.atlassian.net/browse/PYPOST-1454)
4. **`NON-BLOCKER — pre-existing`: Pre-existing lockfile drift**:
   - Jira: [PYPOST-1397](https://pypost.atlassian.net/browse/PYPOST-1397)
   - Test node: `tests/test_lockfile_verification.py::test_repro_check_lock_dev_detects_no_drift`
5. **`NON-BLOCKER — pre-existing`: Makefile test suites time out under parallel load**:
   - Jira: [PYPOST-1413](https://pypost.atlassian.net/browse/PYPOST-1413)
