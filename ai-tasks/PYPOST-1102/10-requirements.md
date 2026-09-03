# PYPOST-1102 Requirements

## Business reason

`MCPProxyServerImpl` forwards MCP requests to upstream servers. Its protocol
methods currently duplicate timing, logging, exception handling, activity
recording, and metrics behavior. The duplication makes future protocol changes
costly and allows operations to drift into inconsistent diagnostics.

## User stories

- As an operator, I want every forwarded MCP operation to retain its current
  timeout, connection-error, and unresolved-variable behavior.
- As an operator, I want proxy activity and metrics to remain consistent across
  tools, prompts, and resources after the dispatch code is consolidated.
- As a maintainer, I want one shared dispatch boundary so protocol methods do
  not need independent copies of common lifecycle behavior.

## Functional requirements

1. The proxy shall provide one shared dispatch mechanism for the standard
   forwarded operations: `list_tools`, `call_tool`, `list_prompts`,
   `get_prompt`, `list_resources`, and `read_resource`.
2. Each operation shall resolve the current proxy headers before connecting to
   the upstream server.
3. Each operation shall use the configured upstream transport and timeout and
   shall preserve the existing per-request connection lifecycle.
4. Successful operations shall return the same upstream-derived values and
   preserve existing tool, prompt, resource, and call-result shapes.
5. Timeout failures shall remain distinguishable from connection failures and
   shall preserve the existing public exception behavior.
6. Unresolved header variables shall abort dispatch before an upstream
   connection is opened and shall preserve the existing exception behavior.
7. Existing MCP activity entries shall retain their operation, outcome,
   duration, argument-count, and sanitized-detail semantics.
8. Existing MCP metrics shall retain request, response, and tool-duration
   tracking semantics, including success and error outcomes for tool calls.
9. Logs shall continue to identify the proxy operation and bounded diagnostic
   metadata without exposing resolved secret header values.
10. The refactor shall not change the registered MCP route paths or the
    supported Streamable HTTP and legacy SSE transports.

## Non-functional requirements

- The common mechanism shall be readable, typed, and compatible with the
  repository's current Python version and async programming model.
- The change shall avoid new runtime dependencies and preserve public method
  signatures used by the server manager and tests.
- The implementation shall not introduce unbounded buffering, shared mutable
  request state, or cross-request leakage of resolved headers.
- Tests added or changed for this task shall declare bounded execution
  timeouts and shall be runnable through the repository Make targets.
- Documentation and task artifacts shall use lines no longer than 100
  characters.

## In scope

- Consolidating common dispatch lifecycle behavior in
  `pypost/core/mcp_proxy_server_impl.py`.
- Preserving or extending focused unit tests for all six forwarded operations,
  success paths, and relevant failure paths.
- Updating developer task artifacts and technical-debt documentation required
  by the top-down workflow.

## Out of scope

- Connection pooling, session reuse, or upstream lifecycle caching (PYPOST-1101).
- A formal shared server-engine interface (PYPOST-1103).
- Replacing the custom-header editor with a key-value table (PYPOST-1104).
- New live multi-process wire integration coverage (PYPOST-1105).
- Changes to upstream MCP protocol semantics, route paths, or authentication
  policy.
- Broad cleanup of unrelated baseline failures or unrelated proxy behavior.

## Acceptance criteria

- All six protocol methods use the approved shared dispatch boundary.
- Existing focused proxy tests pass, including success, timeout, connection,
  unresolved-variable, activity, and metric behavior.
- No raw resolved secret header values appear in logs or activity details.
- The proxy's public method signatures, transport routes, and upstream result
  behavior remain compatible.
- The relevant Make lint, test, type-check, and AI-task verification targets
  pass, with any pre-existing failures documented rather than broadened.
- The implementation is committed with a Jira-keyed conventional commit and
  the Jira issue is transitioned to Done only after review gates pass.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Shared error handling changes exception identity or messages. | Preserve explicit exception mapping and test each failure class. |
| Generic dispatch loses operation-specific result normalization. | Keep normalization callbacks or adapters close to each method. |
| Activity details accidentally include secrets. | Reuse existing sanitization and assert raw values are absent. |
| Metrics are recorded twice or omitted. | Add call-count assertions for success and failure paths. |
