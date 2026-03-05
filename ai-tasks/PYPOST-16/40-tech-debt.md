# PYPOST-16: Technical Debt Analysis

## Shortcuts Taken

- **No Arguments Support**: Tools exposed via MCP do not accept arguments. They execute the request exactly as configured in PyPost (with current environment variables). This limits flexibility (agent cannot pass ID dynamically).
    - *Future*: Parse `{{variable}}` in request and generate JSON Schema for tool arguments.
- **Restart on Update**: When the list of tools (requests) changes, the server might need a restart or explicit update notification to clients (if supported by MCP). Currently, we might rely on the agent polling `list_tools`.
- **Single Environment**: The server uses the currently active environment in PyPost. If the user switches environment in UI, the server starts using new variables. This might be unexpected for the agent if it relies on state.
- **Thread Safety**: We are running `asyncio` server in a thread and calling PyPost core logic (which might be synchronous or use Qt). Need to ensure `HTTPClient` is thread-safe or instantiated per request.

## Missing Tests

- No automated tests for MCP server interaction. Testing is manual via MCP Inspector or Cursor.

## Follow-up Tasks

- Implement argument parsing for tools.
- Add logging/inspection of MCP calls in UI.
- Add tests using an MCP client mock.
