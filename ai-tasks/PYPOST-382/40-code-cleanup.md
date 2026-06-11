# PYPOST-382: Code Cleanup

## Lint and format

- No new linter warnings in modified files.
- Constructor signatures follow existing optional-parameter style (`| None = None`).
- Debug log messages match existing `id=%d` injection tracing pattern from PYPOST-378.

## Review notes

- Post-construction attribute assignment in existing tests left unchanged (backward compatible).
- No unused imports added.
- Line length within 100 characters.

## Files touched

| File | Change |
| --- | --- |
| `pypost/core/request_service.py` | Optional `http_client`, `mcp_client` params |
| `pypost/core/http_client.py` | Optional `session` param |
| `tests/test_request_service.py` | Two injection tests |
| `tests/test_http_client.py` | One injection test |
| `tests/test_main_window.py` | One DI retention test |
| `doc/dev/testability.md` | New developer guide |
