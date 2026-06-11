# PYPOST-156: Code Cleanup

## Changes

- Removed duplicate nested endpoint classes from `mcp_server_impl.py` and `metrics_server.py`.
- Dropped unused imports (`SseServerTransport`, `Route`, `Response`, `MCP_LEGACY_SSE_MESSAGES_PATH`).
- Added focused `tests/test_mcp_legacy_sse.py` with `pytestmark` timeout.

## Verification

- `pytest tests/test_mcp_legacy_sse.py tests/test_mcp_server_impl.py` — 39 passed.
