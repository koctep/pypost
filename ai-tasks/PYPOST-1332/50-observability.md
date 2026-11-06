# PYPOST-1332: Observability Implementation

## Observability Decision

PYPOST-1332 extends the fail-closed path-segment guard in
`HTTPClient._prepare_request_kwargs` to reject blank segments. The critical operational
event is an HTTP request blocked before `session.request` because a rendered path segment
is empty (mid-path `//` or trailing blank).

Step 4 emits a structured ERROR log with an origin-bounded URL
(`blank_path_segment_rejected`), parallel to PYPOST-1346’s `dot_path_segment_rejected`.
Step 6 documents that surface, registers the event for CI log guardrails, and keeps the
focused log-safety regression. No new metric schema: existing request-error tracking
covers the MCP / `RequestService` path.

## Logging Implementation

### Added Logs

- **ERR**: `pypost.core.http_client` emits `blank_path_segment_rejected` when the path
  helper raises `ExecutionError(TEMPLATE)` with blank-segment detail during
  `_prepare_request_kwargs`. Fields:
  - `method=<HTTP method>`
  - `url=<origin-only>` via `HTTPClient._template_error_log_url` (scheme, hostname, valid
    explicit port; userinfo / path / query / fragment omitted; malformed →
    `[invalid-url]`; capped at 512 characters)
  - Does **not** log the full rendered path, headers, params, body, or environment map

Dot rejects continue to use `dot_path_segment_rejected` unchanged.

No **EMERG**, **ALERT**, **CRIT**, **NOTICE**, **INFO**, or **DEBUG** event is needed for
a rejected caller-controlled blank path segment.

### Log Structure

- Structured logs: yes — stable event name with `key=value` fields
- Includes context: yes — HTTP method + bounded origin only
- Log levels: `ERROR` at the outbound rejection boundary
- Large/sensitive data: path, query, fragment, credentials omitted (same helper as
  `template_integer_conversion_failed` / `dot_path_segment_rejected`)

### Related existing logs (unchanged)

MCP callers still surface rejection through `ExecutionError` → structured tool result
(`error: true`, `error_category=template`). Upstream `request_execution_failed` may fire
when `RequestService` catches the error.

## Metrics Implementation (if applicable)

### Performance Metrics

No new performance metrics. Pre-dispatch reject; existing
`track_request_error(ErrorCategory.TEMPLATE)` covers the RequestService path.

### Business Metrics

None. Blank-segment rejection is a validation outcome, not a business conversion event.

### System Health Metrics

None.

## Monitoring Integration

- [x] Prometheus metrics — reuse existing TEMPLATE request-error counters (no new series)
- [ ] Grafana dashboards — no task-specific dashboard
- [ ] Alerting rules — agent misuse via ERROR logs; not a service-health alert alone
- [x] Log aggregation — `blank_path_segment_rejected` available when app logs are collected
- [x] CI test log guardrails — prefix registered in `tests/expected_log_allowlist.yaml`;
  `baseline_error_count` raised 164 → 165 for the intentional assertLogs ERROR

## Validation Results

- [x] Logs correctly formatted — `blank_path_segment_rejected method=… url=…`
- [x] Metrics — N/A for new series; documented reuse of `track_request_error(TEMPLATE)`
- [x] assertLogs regression in `TestHTTPClientBlankPathSegmentRejection`
- [x] Origin-only URL; path omitted from ERROR line
- [x] Allowlist rule `pypost.core.http_client` / `blank_path_segment_rejected`
- [x] Focused tests via `make test` (see roadmap)

## Notes

- Event selection uses `detail.startswith("Blank path segment")` so blank and dot share
  one helper without a second exception type.
- `%2e` lookalikes remain out of scope (PYPOST-1346 debt).
