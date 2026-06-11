# PYPOST-549: Observability (Step 5)

Epic-level observability vision for the MCP Tools program.

## Operator observability (in scope)

- **Prometheus** at `/metrics` on the metrics port (default 9080): request volume, MCP tool
  usage, and error counters — for the PyPost operator on the local machine.
- **Not in scope for agents**: operational events are not streamed to the AI agent; context
  belongs in each tool response (README Vision / epic principles).

## Delivered (child stories)

| Item | Story | Notes |
| --- | --- | --- |
| MCP request/response counters | Pre-PYPOST-549 / PYPOST-44 | `track_mcp_*` in `mcp_server_impl.py` |
| Streamable HTTP connection logging | PYPOST-551 | URLs reflect `/mcp` in client paths |
| Env-var injection debug logs | PYPOST-550 | `_build_execution_variables` DEBUG |

## Planned (child stories)

| Item | Story |
| --- | --- |
| User-facing Prometheus documentation | PYPOST-561 |
| MCP server health gauge, call latency histogram | PYPOST-562 |
| Mask secrets in MCP logs/diagnostics | PYPOST-554 |
| MCP call inspection in UI | PYPOST-141 (debt, related) |

## Worklog

role: execution, step: 5, step_name: Observability, tokens_used: (subagent aggregate)
