# PYPOST-160: Observability

## Assessment

No new logging or metrics required. Endpoint extraction (PYPOST-156) moved existing ASGI
handlers to a shared module without changing request paths, handlers, or metric
instrumentation.

## Existing coverage

MCP request/response metrics remain in `MCPServerImpl.call_tool` and `MetricsServer` resource
handlers — unchanged.
