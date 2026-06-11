# PYPOST-367: Technical Debt Analysis

## Shortcuts Taken

- Routing tests avoid live GET `/sse` and POST `/sse/messages` because both block on SSE
  transport. Structure and HTTP method guards are asserted instead.

## Code Quality Issues

- None blocking for this ticket.

## Missing Tests

- Live MCP client integration (tool list + call over SSE) — [PYPOST-368](https://pypost.atlassian.net/browse/PYPOST-368)
- End-to-end GET `/sse` handshake in TestClient — deferred; would need transport mocks or
  async timeout harness.

## Performance Concerns

- None.

## Follow-up Tasks

- None new. PYPOST-368 and PYPOST-370 remain the integration-test follow-ups from PYPOST-38.
