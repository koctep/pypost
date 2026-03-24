# PYPOST-16: Technical Debt Analysis


## Shortcuts Taken

- **No Arguments Support**: Tools exposed via MCP do not accept arguments. They execute the request exactly as configured in PyPost (with current environment variables). This limits flexibility (agent cannot pass ID dynamically). — [PYPOST-135](https://pypost.atlassian.net/browse/PYPOST-135)
    - *Future*: Parse `{{variable}}` in request and generate JSON Schema for tool arguments.
- **Restart on Update**: When the list of tools (requests) changes, the server might need a restart or explicit update notification to clients (if supported by MCP). Currently, we might rely on the agent polling `list_tools`. — [PYPOST-136](https://pypost.atlassian.net/browse/PYPOST-136)
- **Single Environment**: The server uses the currently active environment in PyPost. If the user switches environment in UI, the server starts using new variables. This might be unexpected for the agent if it relies on state. — [PYPOST-137](https://pypost.atlassian.net/browse/PYPOST-137)
- **Thread Safety**: We are running `asyncio` server in a thread and calling PyPost core logic (which might be synchronous or use Qt). Need to ensure `HTTPClient` is thread-safe or instantiated per request. — [PYPOST-138](https://pypost.atlassian.net/browse/PYPOST-138)

## Missing Tests

- No automated tests for MCP server interaction. Testing is manual via MCP Inspector or Cursor. — [PYPOST-139](https://pypost.atlassian.net/browse/PYPOST-139)

## Follow-up Tasks

- Implement argument parsing for tools. — [PYPOST-140](https://pypost.atlassian.net/browse/PYPOST-140)
- Add logging/inspection of MCP calls in UI. — [PYPOST-141](https://pypost.atlassian.net/browse/PYPOST-141)
- Add tests using an MCP client mock. — [PYPOST-142](https://pypost.atlassian.net/browse/PYPOST-142)
