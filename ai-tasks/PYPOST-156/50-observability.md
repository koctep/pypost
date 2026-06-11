# PYPOST-156: Observability

## Assessment

No new logging or metrics required. This refactor moves existing ASGI handlers to a shared
module without changing request paths, handlers, or metric instrumentation.

## Existing coverage

MCP request/response metrics remain in `MCPServerImpl.call_tool` and `MetricsServer` resource
handlers — unchanged by this task.
