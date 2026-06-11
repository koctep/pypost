# PYPOST-553: Observability (Step 5)

## Existing signals

No change to MCP request/response metrics (`track_mcp_request_received`,
`track_mcp_response_sent`). Metadata affects `list_tools` only — not execution path.

## Logging

No new log lines required. Tool description and param counts are not sensitive; schema
generation remains synchronous at `list_tools` time (same as before).

## Future (optional)

If operators need visibility into schema generation failures, a DEBUG log with
`tool_name` and `param_count` could be added — deferred as non-essential for this story.

## Verdict

Observability unchanged and acceptable for scope.
