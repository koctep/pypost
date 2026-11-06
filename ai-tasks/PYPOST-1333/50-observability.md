# PYPOST-1333: Observability Implementation

## Decision

**No new events or metrics.** This task hardens existing log/alert sinks so rendered
URL secrets cannot appear in them. Event names, field sets, and levels are unchanged.

## Logging Implementation

### Changed Logs

- **DEBUG** — `http_client.sse_stream_detected`
  - Before: `url=` raw rendered URL.
  - After: `url=` via `HTTPClient._error_log_url(url, variables)` (same sanitizer as
    ERROR / `response_body_truncated`).
- **WARNING** — `request_service.retryable_error`
  - `error=` now uses `_log_safe_error_message(exc.message)` (`sanitize_text`).
  - Combined with sanitized timeout/connection messages raised from `HTTPClient`,
    query secrets no longer appear.
- **WARNING** — `request_service.retry_exhausted`
  - `error=` likewise uses `_log_safe_error_message(error.message)`.

### Unchanged (already safe or out of scope)

- **ERR** — `http_request_timed_out` / `http_connection_failed` / `http_request_failed`
  — already used `_error_log_url` (PYPOST-741).
- **WARNING** — `response_body_truncated` — already `_error_log_url` (PYPOST-1122).
- Retry `url=%r` fields remain the **template** URL (no rendered secrets).

### Levels Not Used

- **EMERG / ALERT / CRIT / NOTICE / INFO**: N/A — no new operational events.

## Metrics Implementation

None added or changed. `track_request_retry_exhaustion(request.url)` continues to
label by template URL.

## Alerts

- `AlertPayload.final_error_message` now receives the log-safe error message
  (covers the PYPOST-1334 scope note). `endpoint` remains the template URL.

## Validation

| Scenario | Evidence |
| --- | --- |
| SSE DEBUG redacts query token | `TestHTTPClientSSEStreamLogging` |
| Timeout/connection message redacts | `TestHTTPClientErrorLogging` message tests |
| Retry WARNING + exhaustion alert | `TestRetryLogSanitization` |
| Truncation WARNING still redacted | existing PYPOST-1122 test |

## Notes

Primary fix is sanitize-at-raise in `HTTPClient` so UI error text, retry logs, and
alerts share one safe message. `request_service` `sanitize_text` is defense in depth
for injected `ExecutionError` values that still carry query-token patterns.
