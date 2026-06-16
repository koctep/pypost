# PYPOST-726: Developer Documentation — asyncio loop teardown

## Overview

Background MCP and metrics servers run uvicorn on a dedicated thread with a private
`asyncio` event loop. SSE transports (`sse_starlette`) may leave a long-lived
`_shutdown_watcher` task pending when `uvicorn.Server.serve()` returns. Closing the
loop without draining those tasks causes asyncio to log
`Task was destroyed but it is pending!` at error level.

`drain_pending_tasks` in `pypost/core/server_bind.py` cancels and awaits all pending
tasks on the loop before `loop.close()`, eliminating the spurious warning.

## Architecture

- **`server_bind.drain_pending_tasks`**: shared helper called from each
  `_run_uvicorn` `finally` block.
- **`MCPServerManager._run_uvicorn`** (`mcp_server.py`): production MCP server thread.
- **`MetricsServer._run_uvicorn`** (`metrics_server.py`): metrics server thread.
- **`LiveMCPServer._run_uvicorn`** (`tests/helpers/mcp_live_server.py`): test harness
  mirror of the production pattern.

## API / Usage

### `drain_pending_tasks(loop: asyncio.AbstractEventLoop) -> None`

Cancel and await any tasks still pending on `loop` before closing it.

- **Call site**: immediately before `loop.close()` on the same thread that owns the
  loop.
- **Idempotent**: no-op when `asyncio.all_tasks(loop)` is empty.
- **Contract**: synchronous; internally uses `loop.run_until_complete(gather(...))`.

## Configuration

None.

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `Task was destroyed but it is pending!` after server stop | Loop closed with pending background tasks | Ensure `drain_pending_tasks(loop)` runs in `finally` before `loop.close()` |
| Shutdown hangs | A pending task ignores cancellation | Investigate the task; this helper cancels all pending tasks |

## Verification

```bash
make test PYTEST_ARGS="tests/test_server_bind.py tests/test_mcp_server_manager.py tests/test_metrics_server_unit.py -q"
```

Regression tests force a never-completing task on the loop and assert no destroyed-task
warning after `_run_uvicorn` completes.
