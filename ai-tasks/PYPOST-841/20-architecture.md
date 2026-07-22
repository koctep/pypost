# PYPOST-841: Architecture

## Decision

Wrap the resource-allocating body of `AgentAppSession.start` so **any** exception
after temp dirs / metrics port / compose begins triggers `shutdown()` before
re-raise. Keep existing ready-timeout logging; generalize cleanup beyond
`TimeoutError` only.

## Approach

```text
start():
  allocate app, temps, metrics_port
  try:
    compose → show → wait ready
    mark _started
    return self
  except BaseException:
    shutdown()   # idempotent; cleans temps + metrics + window
    raise
```

Ready-timeout can keep its warning log inside the wait path or as a specialized
branch before the generic cleanup — cleanup must always run.

## Failing Repro

1. Monkeypatch `wait_until` to raise `RuntimeError` (not `TimeoutError`).
2. Call `start()`; expect the error.
3. Assert: `_temp_dirs` empty, `_composed` is None, metrics port bindable
   (socket) and/or `stop_server` already invoked.

Current code fails step 3 because only `TimeoutError` calls `shutdown()`.

## Risks

- Double-shutdown: `shutdown()` is already idempotent via `_shut_down`.
- Masking original exception: never swallow; always re-raise after cleanup.
