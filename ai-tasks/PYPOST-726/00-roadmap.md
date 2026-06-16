# Roadmap: PYPOST-726

**Programming language:** Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation** (auto-approved
      under autonomous sprint-task-runner mode — see "Approval" section in
      `10-requirements.md`)
- [x] **STEP 2: High-Level Architecture Design** (auto-approved under
      autonomous sprint-task-runner mode — no human reviewer available in
      this run)
- [x] **STEP 3: Development**
  - [x] Verified pre-existing `drain_pending_tasks(loop)` helper in
        `pypost/core/server_bind.py` and its call sites in
        `pypost/core/mcp_server.py` (`MCPServerManager._run_uvicorn`),
        `pypost/core/metrics_server.py` (`MetricsServer._run_uvicorn`), and
        `tests/helpers/mcp_live_server.py` (`LiveMCPServer._run_uvicorn`)
        match the architecture doc exactly — no code changes needed to the
        implementation itself.
  - [x] Added a unit test suite `TestDrainPendingTasks` in
        `tests/test_server_bind.py` covering: cancel+await of a pending
        task, the no-pending-tasks early-return no-op, and that a
        cancelled task gets to run its cleanup/`except CancelledError`
        path before the loop closes.
  - [x] Added regression tests
        `test_run_uvicorn_drains_pending_task_without_destroyed_warning`
        to `tests/test_mcp_server_manager.py` and
        `tests/test_metrics_server_unit.py`: each mocks `uvicorn.Server.serve`
        to leave a never-completing task on the loop (mirroring
        sse_starlette's `_shutdown_watcher`), runs `_run_uvicorn()`, force
        a GC pass, and asserts no "Task was destroyed but it is pending"
        warning is emitted.
  - [x] Ran full suite: `QT_QPA_PLATFORM=offscreen pytest tests/ -m "not slow"`
        → **1488 passed, 1 deselected, 1 unrelated warning** (pre-existing
        `StarletteDeprecationWarning`), 0 failures, no destroyed-task
        warnings anywhere in output.
  - [x] `flake8 pypost/` (CI lint scope) clean on all touched production
        files (`server_bind.py`, `mcp_server.py`, `metrics_server.py`).
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-726/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-726/20-architecture.md`

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-726/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-726/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-726/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/`

## Suggested Branch

`fix/PYPOST-726-mcp-asyncio-teardown-warnings`
