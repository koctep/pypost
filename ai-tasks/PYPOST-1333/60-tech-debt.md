# PYPOST-1333: Technical Debt Analysis

## Shortcuts Taken

- **Defense-in-depth without variables.** `RequestService` applies `sanitize_text`
  without env vars (it never receives resolved variables). Env-value redaction for
  secrets that appear only as path segments therefore depends on sanitize-at-raise in
  `HTTPClient`. Acceptable for this ticket’s stated query-secret threat model; a
  future improvement could thread log-safe context on `ExecutionError`.
- **UI timeout/connection text is redacted.** Chose sanitize-at-raise over a separate
  `log_message` field to avoid a dual-message API. Operators/users see `token=***` in
  the error string. Preferable to leaking secrets into any sink.

## Code Quality Issues

- `_log_safe_error_message` is a one-liner wrapper; kept for call-site clarity at the
  two WARNING / alert sites. Could inline later if desired — not worth a ticket.
- `_error_log_url` name still says “error” while WARNING/DEBUG also use it
  (same note as PYPOST-1122). Rename remains optional debt; no new ticket.

## Missing Tests

- No dedicated caplog test that injects a raw-URL `ExecutionError` into
  `RequestService` without going through `HTTPClient` (defense-in-depth only).
  Covered indirectly when HTTPClient raises; optional follow-up if desired — **no**.
- `retry_exhausted` log line is covered via the same execute path as
  `retryable_error` + alert assertions; no separate assertLogs case — accepted.

## Performance Concerns

None. Sanitization runs only on error / SSE-detect paths.

## Follow-up Tasks

1. `NON-BLOCKER — pre-existing` — `make lint` / `lint-tests` fails on
   `tests/test_mcp_server_registry.py:308` E501 (line > 100). Reproduces with
   `make lint` on the task base tree without this change. Related existing ticket:
   [PYPOST-1303](https://pypost.atlassian.net/browse/PYPOST-1303) (`make lint` does
   not flake8 `tests/` in the production sense; baseline checker still flags this
   occurrence). Do not re-file unless triage shows a new key is needed.

No new product follow-ups from this change. PYPOST-1122 and path-segment tickets
remain orthogonal and already resolved/separate.
