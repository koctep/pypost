# PYPOST-720: Architecture

## test_script_executor.py

`ScriptContext` and `ScriptExecutor` are pure Python — no Qt, no network.
Tests use `unittest.TestCase` with no mocking needed.

## test_metrics_server_unit.py

Tests instantiate `MetricsServer` directly (bypassing `MetricsManager`) to reach
paths that the facade's eager handler registration prevents reaching through the
public API. Key techniques:
- `asyncio.run()` for async methods
- `patch.object(server, "_create_app", ...)` for exception paths
- `patch("uvicorn.Server.serve", serve_noop)` for unexpected-exit path
