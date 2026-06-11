# PYPOST-411: Code Cleanup

## Changes

- Replaced heuristic error classification (`type(exc).__name__` and message substring checks)
  with explicit `httpx` `except` clauses ordered by exception hierarchy.
- Removed unused `MagicMock` import from `tests/test_mcp_client_service.py`.
- Moved `asyncio` import to module level in tests.

## No further cleanup required

- No dead code introduced.
- No new helpers added; inline `except` chain mirrors `http_client.py` style.
- Line length within 100 characters.
