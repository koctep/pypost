# PYPOST-430: Code Cleanup (Step 4)

## Lint and format

- No new linter issues in `http_client.py` or `tests/test_http_client_sse_probe.py`.
- Helpers `_is_sse_content_type` and `_headers_accept_event_stream` are module-level pure
  functions (testable, no class state).

## Review checklist

| Item | Status |
| --- | --- |
| Removed dead `is_sse_endpoint` variable | Done |
| Log key renamed `sse_probe_detected` → `sse_stream_detected` | Done |
| Tests renamed to reflect content-type semantics | Done |
| No unrelated refactors in `HTTPClient` | Done |

## Files touched

- `pypost/core/http_client.py`
- `tests/test_http_client_sse_probe.py`
