# PYPOST-1105 Code Cleanup

## Review

- The new process harness uses top-level spawn targets so it works with the
  `spawn` multiprocessing context.
- Ports are allocated on loopback through the existing test helper.
- Startup waits and process joins are bounded; a remaining exact child is
  terminated and joined again.
- Async MCP clients close their HTTP, transport, and session contexts.
- No production source, dependency, or Makefile changes were required.

## Checks

- `make test-slow PYTEST_ARGS="tests/test_mcp_proxy_live_integration.py -m slow"`
  — 2 passed.
- `make lint` — passed.
- `make typecheck` — passed with the existing baseline unchanged.
- `make verify-ai-tasks` — passed.
