# Architecture: PYPOST-24 - MCP Metrics

## Research
We already have `MetricsManager` from PYPOST-14. We need to add new metrics definitions and expose methods to track them.

## Implementation Plan

1.  **Update `MetricsManager`**:
    -   Define `mcp_requests_total` (Counter).
    -   Define `mcp_request_duration_seconds` (Histogram).
    -   Add `track_mcp_request(tool_name, status, duration)` method.

2.  **Update `MCPServerImpl`**:
    -   In `call_tool` method:
        -   Start timer.
        -   Execute tool.
        -   Stop timer.
        -   Call `MetricsManager.track_mcp_request`.

## Architecture

### `MetricsManager`

```python
self.mcp_requests = Counter('pypost_mcp_requests_total', 'Total MCP requests', ['tool', 'status'])
self.mcp_duration = Histogram('pypost_mcp_request_duration_seconds', 'MCP request duration', ['tool'])
```

### `MCPServerImpl`

```python
start_time = time.time()
try:
    result = await self._execute_tool(...)
    status = "success"
except Exception:
    status = "error"
    raise
finally:
    duration = time.time() - start_time
    metrics_manager.track_mcp_request(tool_name, status, duration)
```
