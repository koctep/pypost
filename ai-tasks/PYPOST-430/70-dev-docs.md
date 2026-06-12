# PYPOST-430: Dev Docs (Step 7)

## Updates

### `doc/dev/request_execution.md`

- Template rendering section: SSE routing described as Content-Type based, not URL heuristic.
- Added note on `Accept: text/event-stream` pre-request timeout tuning.

## Verification

- `make test` — `tests/test_http_client_sse_probe.py` passes.
- No user-facing `doc/mcp_integration.md` change required (agent transport docs unchanged).
