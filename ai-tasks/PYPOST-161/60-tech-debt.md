# PYPOST-161: Technical Debt Analysis

## Shortcuts Taken

None — tests only.

## Code Quality Issues

None introduced.

## Missing Tests

- **Streamable HTTP method guards** — `/mcp` accepts any HTTP method at the Starlette layer;
  SDK handles protocol errors. No follow-up unless product requires explicit 405.

## Performance Concerns

None.

## Follow-up Tasks

None — closes PYPOST-21 item "Add tests for ASGI compatibility of endpoints."
