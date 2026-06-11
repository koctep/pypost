# PYPOST-152: Code cleanup

## Changes

- Added `pypost/core/mcp_transport_routes.py` (single source of route path constants).
- Replaced six hardcoded path strings across `mcp_server_impl.py` and `metrics_server.py`.
- Moved `MCP_STREAMABLE_HTTP_PATH` definition from `mcp_streamable_http.py` to the new module
  (import re-export preserved in streamable helper).
- Tests import constants instead of repeating `/sse`, `/messages`, `/mcp`.

## Verification

- No new lint issues in touched files.
- Focused diff; no unrelated refactors.

## Worklog

role: execution, step: 4, step_name: Code cleanup, tokens_used: 900
