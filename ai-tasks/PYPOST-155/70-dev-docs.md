# PYPOST-155: Dev Docs

## Updates

- `doc/dev/mcp_integration.md`: added subsection on legacy SSE routing (`Route` method filters,
  ASGI delegates, outer `/sse` mount).

## Rationale

Operators and contributors need to know why `/messages` uses ASGI classes on `Route` rather than
request/response handlers.
