# PYPOST-430: Observability (Step 5)

## Logging changes

### `sse_stream_detected` (DEBUG)

Emitted in `send_request` **after** response headers when GET + SSE content-type is detected:

```
sse_stream_detected method=GET url=http://host/path content_type=text/event-stream
```

**Why it matters:** confirms routing to `_handle_sse_response` based on server headers, not URL
shape. Includes `content_type` for triage when servers send parameters (e.g. charset).

### Removed: `sse_probe_detected`

Pre-request URL heuristic log removed with the heuristic itself.

## Metrics

No new metrics. Existing `track_request_sent` / `track_response_received` unchanged.

## Unchanged

- Error logs for timeout, connection, and request failures remain as before.
- `request_complete` debug log still applies to non-SSE responses.
