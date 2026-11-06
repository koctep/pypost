# PYPOST-1362: Stabilize failed-bind registry test against thread cleanup race

## Research

### Observed defect

- Flaky node: `tests/test_mcp_server_registry.py::test_failed_bind_is_reported_for_only_the_requested_instance`
- Failure at baseline `0890b8dc` (before PYPOST-1436): `assert not …is_running()` saw `True` after `wait_for_state(..., "failed")` while uvicorn logged `[Errno 98]` / `mcp_server_start_failed`.
- At that baseline, `MCPServerManager.is_running()` was thread-liveness only (`_server_thread is not None and is_alive()`). Bind failure emits `start_failed` / status `failed` from `_notify_start_failed` **before** `_run_uvicorn` finishes its `finally` (drain loop / close). The worker can still be `is_alive()` for a short window → immediate `is_running()` races cleanup.
- PYPOST-1436 later added `and self._start_error is None` to `is_running()`, which masks most flakes (`is_running` False once the error is recorded). Probe on current tree (50 iterations): `is_running` never True after `failed`, but worker still alive in **1/50** runs and **`_server_thread` is never cleared** after a failed bind (ref retained to a dead or dying thread).

### Lifecycle semantics (confirmed)

| Condition | Expected |
| --- | --- |
| Requested instance bind fails (port busy) | Registry status `failed` with instance id + port in message |
| After failure is reported | That instance `is_running() is False` (settled; not a transient “still starting”) |
| Worker after failed start | Exits and drops its live-thread bookkeeping so liveness and `is_running` agree once settled |
| Sibling instance already running | Remains running / reachable; not stopped by the peer’s failed bind |

Do **not** weaken the “not running after failed bind” assertion. Do **not** use unbounded sleeps.

### Prior art in-repo

- `MCPServerRegistry.wait_for_state` — bounded poll (`timeout`, `time.sleep(0.02)`).
- `tests.helpers.qt_wait.wait_until` / `pypost.agent.ui_wait.wait_until` — bounded predicate waits.
- Adaptive join + retain-on-timeout for **stop** paths (PYPOST-1196 / PYPOST-1437) — different concern; failed-start should not pretend the server is running.

### External notes

- Python `Thread.is_alive()` is false only after `run()` returns; callers must not treat “failure signaled” as “thread already joined” without a happens-before (join or end-of-`run` cleanup).
- Prefer bounded deadline polls over fixed `sleep(N)`.

## Implementation Plan

1. **Production (minimal)** — In `MCPServerManager._run_uvicorn`, at the end of the worker (after `finally` cleanup), if `self._server_thread is threading.current_thread()`, set `self._server_thread = None`. Preserves start-failure notification order; settles bookkeeping when the worker actually exits so post-failure liveness matches “not running” once the thread is done. Keep existing `_start_error` gate on `is_running()` (defense in depth; do not remove).
2. **Registry/test helper** — Reuse bounded polling: after `wait_for_state(id, "failed")`, poll until `not registry.is_running(id)` with a short explicit timeout (same style as `wait_for_state`, e.g. ≤2–5s). Prefer a tiny local helper or `wait_for_state`-adjacent method only if it stays ≤ few lines and is reused; otherwise inline deadline loop in the test module to avoid API sprawl.
3. **Harden the existing isolation test** — Keep all asserts (failed state, alpha still running, beta not running, tools list, failure message contains id + port). Insert bounded not-running wait **between** failed-state wait and the hard `assert not is_running(...)`. No assertion removal/softening.
4. **Deterministic red coverage (Step 3)** — Add a focused test that forces failure notification while the worker is still finishing (Event/hold after `_notify_start_failed` via monkeypatch of `_run_uvicorn`), then releases and asserts: after bounded settle, `not is_running` and `_server_thread is None` (or equivalent public “no live worker” check). Fails today because the ref is retained after exit; passes after Step 4 clear-on-exit.
5. **Observability** — Rely on existing `mcp_server_start_failed` / `mcp_registry_status`; no new noisy logs unless a clear settle diagnostic is needed at DEBUG.
6. **Docs** — Note failed-bind settle semantics in `doc/dev` MCP lifecycle docs (isolation + bounded wait / thread clear).

**Mandatory — Failing Repro (Step 3):**

- **What**: Automated test asserting that after a forced bind-style start failure, once the worker is allowed to finish, the manager’s server-thread reference is cleared (`None`) and `is_running()` is False, while a peer remains running when applicable—or a single-manager unit variant without peer if simpler.
- **Where**: `tests/test_mcp_server_registry.py` (adjacent to `test_failed_bind_is_reported_for_only_the_requested_instance`) or a small dedicated module under `tests/` if fixtures demand it.
- **How to force**: Monkeypatch `MCPServerManager._run_uvicorn` to call `_notify_start_failed(...)`, block on a `threading.Event`, then return—no live uvicorn/port required for the unit path. Integration path may still use occupied socket for the existing test.
- **Sequencing**: research → red test (ref still set after exit) → clear-on-exit + bounded wait in isolation test → green.

## Architecture

```mermaid
sequenceDiagram
    participant Test
    participant Registry
    participant Manager
    participant Worker as ServerThread

    Test->>Registry: start(beta) port busy
    Registry->>Manager: start_server
    Manager->>Worker: start _run_uvicorn
    Worker->>Manager: _notify_start_failed (sets _start_error)
    Manager->>Registry: start_failed / status failed
    Note over Worker: still in finally / alive briefly
    Test->>Registry: wait_for_state(failed)
    Test->>Registry: bounded wait until not is_running
    Worker->>Manager: end of run: _server_thread = None
    Test->>Registry: assert not is_running(beta); alpha still up
```

### Modules

| Module | Responsibility |
| --- | --- |
| `pypost/core/qt/mcp_server.py` | Worker lifecycle; notify failure; clear `_server_thread` on worker exit |
| `pypost/core/mcp_server_registry.py` | Per-instance status; isolation; optional thin wait helper |
| `tests/test_mcp_server_registry.py` | Isolation + settle coverage; bounded waits; no unbounded sleep |

### Patterns

- **Happens-before via worker exit**: clear thread ref only on the worker’s own exit path (not from the test thread racing `is_alive`).
- **Defense in depth**: `_start_error` keeps `is_running` False as soon as failure is known; thread clear settles bookkeeping after exit.
- **Bounded polling**: deadline + short sleep, mirroring `wait_for_state`.

## Q&A

- Q: Can we only fix the test with a sleep?
  A: No unbounded/fixed long sleeps. Bounded deadline poll only; prefer production clear-on-exit so settle is deterministic.
- Q: Remove `_start_error` from `is_running`?
  A: No — keep it; the race window before thread exit still needs an immediate False.
- Q: Weaken `assert not is_running`?
  A: No — keep the assert; only precede it with a bounded wait for settle.
