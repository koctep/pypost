# PYPOST-788: Observability

## Scope

Documentation-only change. No runtime logging, metrics, or tracing added.

## Related packages in updated docs

The refreshed setup section documents production packages including:

- `prometheus_client` — default metrics backend
- `mcp` — MCP server SDK (transitive starlette/uvicorn via SDK)

OpenTelemetry remains documented in the optional overlay section (PYPOST-787); not part of the
production summary table.
