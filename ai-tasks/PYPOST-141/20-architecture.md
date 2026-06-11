# PYPOST-141: MCP activity logging architecture

## Research

- `MCPServerImpl.list_tools` and `call_tool` run on the uvicorn asyncio thread; UI updates
  must use Qt signals (`MCPServerManager.activity_recorded`) — same pattern as PYPOST-556
  startup signaling.
- `McpSecretsPolicy.safe_execution_log_fields` already defines count-only diagnostics for
  execution; UI must not display MCP argument values.
- `McpToolsOverviewDialog` provides a read-only table pattern for top-bar MCP dialogs.

## Implementation Plan

1. **`McpActivityLog`** — Thread-safe ring buffer (default 100 entries) with optional
   `on_append` callback.
2. **`McpActivityEntry`** — Immutable record: timestamp, operation, outcome, tool metadata,
   arg count, HTTP status, duration, short error detail.
3. **`MCPServerImpl`** — Accept optional `activity_log`; append on `list_tools` / `call_tool`.
4. **`MCPServerManager`** — Own log, emit `activity_recorded` from callback.
5. **`McpActivityDialog`** — Read-only table; `set_entries` for live refresh.
6. **`EnvPresenter`** — **MCP Activity (N)** button, open dialog, refresh on signal.

## Architecture

```mermaid
flowchart LR
    Agent --> MCPServerImpl
    MCPServerImpl --> McpActivityLog
    McpActivityLog -->|on_append| MCPServerManager
    MCPServerManager -->|activity_recorded| EnvPresenter
    EnvPresenter --> McpActivityDialog
```

## Worklog

role: execution, step: 2, step_name: Architecture, tokens_used: 2800
