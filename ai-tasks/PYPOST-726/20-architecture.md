# PYPOST-726: Clean up spurious server shutdown warnings

## Research

### Root cause confirmation

Traced the warning to `sse_starlette`'s legacy SSE transport
(`/Users/il/src/pypost/.venv/lib/python3.14/site-packages/sse_starlette/sse.py`):

- `_ensure_watcher_started_on_this_loop()` (sse.py:146-156) calls
  `loop.create_task(_shutdown_watcher())` the first time an `EventSourceResponse`
  is created on a given event loop. The watcher is **scoped to whichever loop is
  current when the first SSE response is built**, not to the request/response
  lifecycle.
- `_shutdown_watcher()` (sse.py:110-143) loops `await anyio.sleep(0.5)` until either
  `AppStatus.should_exit` or the introspected uvicorn `Server.should_exit` flips to
  `True`. It is a long-lived background task by design — sse_starlette's own
  mechanism for noticing server shutdown without explicit wiring.
- Both `pypost/core/mcp_server_impl.py:235` and `pypost/core/metrics_server.py:90`
  call `build_legacy_sse_app(...)` (`pypost/core/mcp_legacy_sse.py:45`), so **both**
  the MCP server and the metrics server mount the legacy SSE route and are
  susceptible to this task being created on their respective per-thread event
  loops. `tests/helpers/mcp_live_server.py` runs the same `MCPServerImpl` app, so
  it inherits the identical exposure.
- All three call sites follow the same pattern: a background thread creates a new
  loop (`asyncio.new_event_loop()`), runs `uvicorn.Server.serve()` to completion via
  `loop.run_until_complete(...)`, then closes the loop. `uvicorn.Server.serve()`
  returns once `should_exit` is observed and its own internal tasks are torn down,
  but it has no knowledge of (and does not await) the sse_starlette watcher task,
  which is still mid-`sleep(0.5)` at that point.
- `loop.close()` on a loop that still has a pending `Task` does not raise, but when
  that orphaned `Task` object is later garbage-collected, asyncio's `Task.__del__`
  detects it never finished and logs `Task was destroyed but it is pending!` at
  error level via the default exception handler — this is exactly audit finding
  R-P3-003.

### Why this is generic, not SSE-specific

The requirements (`10-requirements.md`, "Constraints and Assumptions") explicitly
ask for a fix that "generically cover[s] any outstanding shutdown work, not
special-case that one situation." `_shutdown_watcher` is the *known* trigger today,
but uvicorn/Starlette/MCP SDK internals could spawn other loop-scoped background
tasks in the future (e.g. keep-alive pings, other SDK transports). A fix that
enumerates and special-cases only the sse_starlette task would regress the moment
any other library follows the same "background task per loop" pattern — and the
codebase already mounts both the legacy SSE transport and the streamable-HTTP
transport (`pypost/core/mcp_transport_routes.py`) behind the same servers, so
multiple transport implementations share the one loop.

### Alternatives considered

1. **Targeted fix: explicitly cancel only the sse_starlette watcher task.**
   Would require importing sse_starlette internals (`_get_shutdown_state`,
   `AppStatus`, the watcher coroutine function) to identify the task by coroutine
   identity, which are private/unstable APIs not part of sse_starlette's public
   surface. Brittle across sse_starlette version bumps, and explicitly contradicts
   the "do not special-case" constraint. Rejected.

2. **Patch sse_starlette's `AppStatus.should_exit` proactively before
   `loop.close()`.** This only flips the flag the watcher polls; the watcher still
   needs up to 0.5s and one more loop iteration to observe it and exit — and the
   surrounding code calls `loop.close()` immediately after `run_until_complete`
   returns, with no further opportunity to run the loop and let the watcher's next
   poll happen. Would require *also* doing a bounded `run_until_complete` pass,
   which collapses back to needing the same "let pending tasks finish" mechanic
   anyway, but now coupled to sse_starlette's private flag. Rejected as strictly
   worse than alternative 3.

3. **Generic drain: enumerate `asyncio.all_tasks(loop)`, cancel all pending tasks,
   and `run_until_complete(asyncio.gather(..., return_exceptions=True))` before
   `loop.close()`.** This is the approach already implemented in the working-tree
   diff (`drain_pending_tasks` in `pypost/core/server_bind.py`). It:
   - Requires no knowledge of sse_starlette's internals — works against any
     well-behaved asyncio `Task`, present or future.
   - Is bounded: cancellation interrupts `anyio.sleep(0.5)` (or any other await)
     immediately rather than waiting out the poll interval, so it does not slow
     down shutdown.
   - Is the standard, documented pattern for "close a loop you own" cleanup
     (the same idiom `asyncio.run()` uses internally via `_cancel_all_tasks`).
   - Risk: in principle it could cancel a task that is *not* shutdown-watcher noise
     but legitimate unfinished application work. Evaluated below. **Chosen.**

### Risk evaluation: cancelling unrelated pending tasks

At the point `drain_pending_tasks(loop)` runs, `uvicorn.Server.serve()` has already
returned, which means uvicorn's own request lifecycle, lifespan handling, and
graceful-shutdown sequence (closing connections, finishing in-flight responses) are
complete — `serve()` does not return until that finishes. Each of the three call
sites is a single-purpose thread whose only job is to run *this* server's loop;
nothing else schedules independent long-lived work on it. The remaining task set at
this point consists of:
- The sse_starlette `_shutdown_watcher` (confirmed above), and
- Possibly stray completed-but-not-yet-garbage-collected callback tasks from
  connection teardown (these are typically already done, so `cancel()` on a
  finished task is a no-op).

Because the loop is being closed unconditionally in all three call sites
regardless of this change (this is existing, intended behavior — the server is
fully stopping), any task still pending at this point was *already* going to be
abandoned without this change; the only question is whether it is abandoned
noisily (today) or cancelled and awaited cleanly (after the fix). There is no
scenario in the current call sites where letting such a task "run to completion
on its own" instead of cancelling is the correct choice, because nothing reads its
result after the loop closes. This matches the Definition of Done's "given the
opportunity to finish or be cancelled cleanly" — `gather(..., return_exceptions=True)`
gives a cancelled task one chance to run its `except CancelledError` / `finally`
cleanup before the loop goes away, rather than skipping straight to abandonment.

### Public API verification

- No changes to `MCPServerManager`, `MetricsServer`, or `LiveMCPServer` public
  methods, constructors, signals, or return values — `drain_pending_tasks` is
  called only inside existing private `_run_uvicorn` methods, in `finally` blocks,
  immediately before the pre-existing `loop.close()` call.
- No new third-party dependency — `asyncio` is stdlib.
- No transport-visible behavior change — by the time this runs, uvicorn's
  `serve()` has already completed its own client-facing shutdown; this only
  affects bookkeeping internal to the now-finished event loop.

## Implementation Plan

(Already implemented in the working tree; this section documents the plan the
existing diff matches, for Step 3 to validate/finalize against.)

1. Add `drain_pending_tasks(loop: asyncio.AbstractEventLoop) -> None` to
   `pypost/core/server_bind.py` (co-located with `format_bind_error`, since both
   are shared uvicorn-lifecycle helpers used by all three background-thread
   server runners).
2. In `MCPServerManager._run_uvicorn` (`pypost/core/mcp_server.py`) and
   `MetricsServer._run_uvicorn` (`pypost/core/metrics_server.py`), call
   `drain_pending_tasks(loop)` in the existing `finally` block, directly before
   the existing `loop.close()` line. No change to the `try`/`except` branches
   that handle bind errors or unexpected exceptions.
3. In `tests/helpers/mcp_live_server.py`'s `LiveMCPServer._run_uvicorn`, wrap the
   existing `loop.run_until_complete(self._server.serve())` in `try`/`finally`,
   calling `drain_pending_tasks(loop)` then `loop.close()` in `finally` — mirroring
   the production call sites exactly, per the requirement that the test harness
   "mirror the same clean shutdown behavior."
4. No other modules change. `mcp_legacy_sse.py`, `mcp_streamable_http.py`,
   `mcp_server_impl.py` are untouched — the fix lives entirely at the
   loop-teardown boundary, not in transport code.

## Architecture

### Module responsibilities

| Module | Responsibility | Change |
|---|---|---|
| `pypost/core/server_bind.py` | Shared helpers for uvicorn lifecycle in background threads: bind-error formatting (`format_bind_error`) and now loop teardown (`drain_pending_tasks`). | Add `drain_pending_tasks`. |
| `pypost/core/mcp_server.py` (`MCPServerManager`) | Owns the MCP server's background thread + event loop; starts/stops uvicorn; reports status via Qt signals. | Call `drain_pending_tasks(loop)` before `loop.close()` in `_run_uvicorn`'s `finally`. |
| `pypost/core/metrics_server.py` (`MetricsServer`) | Owns the metrics server's background thread + event loop; same lifecycle shape as `MCPServerManager`. | Call `drain_pending_tasks(loop)` before `loop.close()` in `_run_uvicorn`'s `finally`. |
| `tests/helpers/mcp_live_server.py` (`LiveMCPServer`) | Test-only double mirroring `MCPServerManager._run_uvicorn` for integration tests. | Wrap `serve()` call in `try/finally`; call `drain_pending_tasks(loop)` then `loop.close()`. |
| `pypost/core/mcp_legacy_sse.py`, `mcp_server_impl.py`, `mcp_transport_routes.py` | Transport/app construction (source of the sse_starlette watcher task). | No change — confirmed as the trigger, not the fix location. |

### Interaction diagram

```
Background thread (per server)
  loop = asyncio.new_event_loop()
  try:
      loop.run_until_complete(server.serve())   # uvicorn's own graceful shutdown
                                                  # completes here; sse_starlette's
                                                  # _shutdown_watcher task may still
                                                  # be pending (mid anyio.sleep(0.5))
  except OSError / Exception:
      ... existing bind-error / unexpected-exit handling (unchanged) ...
  finally:
      drain_pending_tasks(loop)   # NEW: cancel all pending tasks on `loop`,
                                  #      then run_until_complete(gather(...))
                                  #      to let cancellation unwind cleanly
      loop.close()                # existing — now closes a loop with no
                                  # pending tasks, so no GC-time warning
```

### Public interface

```python
def drain_pending_tasks(loop: asyncio.AbstractEventLoop) -> None:
    """Cancel and await any tasks still pending on `loop` before closing it."""
```

- **Module**: `pypost/core/server_bind.py` (new export, alongside existing
  `format_bind_error`).
- **Contract**: idempotent and safe to call on a loop with zero pending tasks
  (early-returns). Synchronous — internally drives the loop via
  `run_until_complete`, so callers do not need to be inside an active coroutine.
  Must be called on the same thread that owns `loop` (matches all three call
  sites, which already run single-threaded loop owners).
- **Call sites** (all pre-existing `finally` blocks, immediately before the
  pre-existing `loop.close()`):
  - `MCPServerManager._run_uvicorn` — `pypost/core/mcp_server.py`.
  - `MetricsServer._run_uvicorn` — `pypost/core/metrics_server.py`.
  - `LiveMCPServer._run_uvicorn` — `tests/helpers/mcp_live_server.py` (new
    `try/finally` wrapping needed here since this method previously had no
    `finally` at all).
- **No public API surface of `MCPServerManager` / `MetricsServer` / `LiveMCPServer`
  changes** — confirms the Definition of Done constraint that only internal
  teardown sequencing is affected.

### Architectural pattern

This is a **Template Method**–shaped cleanup: all three `_run_uvicorn` methods
already share the same "new loop → run until complete → close loop" skeleton; the
fix adds one shared step to that skeleton via a single extracted helper function
rather than duplicating cancellation logic three times. Keeping the helper in
`server_bind.py` (already the shared home for uvicorn-lifecycle helpers used by
all three sites) avoids introducing a new module and keeps the "shared helpers for
uvicorn lifecycle in background threads" module cohesive.

### Test strategy (for Step 3 to implement/validate)

- **Unit test** of `drain_pending_tasks` in isolation (new test, likely
  `tests/test_server_bind.py` or a dedicated file): create a private event loop,
  schedule a never-completing task (e.g. `asyncio.sleep(100)`), call
  `drain_pending_tasks(loop)`, assert the task is cancelled/done and
  `asyncio.all_tasks(loop)` is empty afterward, then confirm `loop.close()` does
  not raise. Also test the no-pending-tasks early-return path.
- **Regression test** for the original symptom: run a real MCP/metrics server
  start+stop cycle (existing fixtures in `tests/helpers/mcp_live_server.py` and
  any direct `MCPServerManager`/`MetricsServer` lifecycle tests) under
  `pytest -W error::pytest.PytestUnraisableExceptionWarning` or by asserting on
  captured `caplog`/`capsys` that no `"Task was destroyed but it is pending"`
  string appears after shutdown — mirroring how the audit finding was originally
  observed.
- **Existing suite**: full `make test` run to confirm no new flakiness/failures
  and that prior passing tests (bind-error formatting, MCP/metrics lifecycle,
  live-server-backed integration tests) are unaffected, since this only touches
  shutdown-path code that runs after assertions in those tests have already
  completed.

## Q&A

- **Q**: Is "cancel + await all pending tasks on the loop" too broad — could it
  silently swallow a real bug (a task that should have completed but didn't)?
  **A**: At the call point, `uvicorn.Server.serve()` has already returned, meaning
  the server's own request/connection/lifespan shutdown is done. Nothing in the
  current codebase schedules independent long-lived work on these
  single-purpose, per-server background-thread loops. Since `loop.close()`
  already unconditionally follows (today, without this fix, any pending task
  here would be abandoned anyway), `drain_pending_tasks` changes *how* leftover
  tasks are disposed of (cleanly cancelled vs. silently GC'd with a noisy
  warning), not *whether* they are disposed of. If a future change schedules
  meaningful background work on one of these loops without awaiting it before
  `serve()` returns, that is a separate, pre-existing latent bug this fix does
  not introduce or worsen.
- **Q**: Why put `drain_pending_tasks` in `server_bind.py` rather than a new
  module?
  **A**: `server_bind.py` is already the shared home for uvicorn-lifecycle
  helpers (`format_bind_error`) used by exactly these same three call sites; the
  existing diff updated its module docstring from "bind failures" to "lifecycle
  (bind errors, shutdown)" accordingly. No new module is justified for one
  function with the same callers and same lifecycle scope.
- **Q**: Does this affect the streamable-HTTP transport (the non-SSE path)
  mentioned in scope/out-of-scope?
  **A**: No transport-visible behavior changes for either transport — the fix is
  generic and loop-level, applied after `serve()` returns regardless of which
  transport(s) were mounted. It is "in scope" only in the sense that it
  incidentally also drains any stray task that transport might leave pending; it
  does not touch `mcp_streamable_http.py`.
