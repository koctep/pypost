# PYPOST-1362: Technical Debt Analysis

## Shortcuts Taken

- Thread-ref clear uses `self._server_thread is threading.current_thread()` at the end of
  `_run_uvicorn` rather than a dedicated lifecycle helper/API. Adequate for the settle race;
  a shared `_release_server_thread_if_current()` could be extracted if more exit paths appear.
- Isolation test polls with a local `_wait_until_not_running` helper instead of adding a
  public `MCPServerRegistry.wait_until_not_running` API (avoids API sprawl for one consumer).

## Code Quality Issues

- Red/settle coverage asserts `manager._server_thread is None` (private attribute). Prefer a
  narrow public probe later if other modules need the same contract without reaching into
  manager internals.
- `is_running()` still depends on both thread liveness and `_start_error is None`
  (PYPOST-1436). That dual gate is intentional defense in depth; document when changing either
  side.

## Missing Tests

- No dedicated stress loop (N× occupied-port) in CI; manual probe was 50 iterations during
  design. Optional follow-up: parameterized repeat mark if flakes reappear under load.
- Process-mode (`execution_mode=process`) failed-bind settle is out of scope for this thread
  race; existing process isolation coverage remains separate.

## Performance Concerns

- Bounded polls use 20ms sleep (same order as `wait_for_state`); negligible vs uvicorn startup.
- Clear-on-exit is O(1) and only on worker teardown.

## Follow-up Tasks

- None filed (per task instruction: do not create Jira issues). Optional later:
  - Extract public “worker settled / no live server thread” helper if more tests need it.
  - Consider process-runner analogue if a similar failure-signal-vs-cleanup race appears there.
- No pre-existing suite failures filed from this run (target nodes and registry module green
  after the fix).
