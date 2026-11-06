# PYPOST-1346: Observability Implementation

## Observability Decision

PYPOST-1346 adds a fail-closed path-segment guard in
`HTTPClient._prepare_request_kwargs`. The critical operational event is an
HTTP request that is intentionally blocked before `session.request` because a
rendered path segment is exactly `.` or `..`.

Step 4 already emits a structured ERROR log with an origin-bounded URL
(`dot_path_segment_rejected`). Step 6 documents that surface, registers the
event for CI log guardrails, and adds focused log-safety regressions. No new
metric schema is warranted: existing request-error tracking covers the MCP /
`RequestService` path.

## Logging Implementation

### Added Logs

- **ERR**: `pypost.core.http_client` emits `dot_path_segment_rejected` when
  `_assert_no_dot_path_segments` raises `ExecutionError(TEMPLATE)` during
  `_prepare_request_kwargs`. Fields:
  - `method=<HTTP method>`
  - `url=<origin-only>` via `HTTPClient._template_error_log_url` (scheme,
    hostname, valid explicit port; userinfo / path / query / fragment omitted;
    malformed URLs → `[invalid-url]`; capped at 512 characters)
  - Does **not** log the rejected segment value, full rendered path, headers,
    params, body, or environment variable map

No **EMERG**, **ALERT**, **CRIT**, **NOTICE**, **INFO**, or **DEBUG** event is
needed for a rejected caller-controlled path segment. Successful requests keep
the existing `request_complete` DEBUG path unchanged.

### Log Structure

Log format used:
- Structured logs: yes — stable event name with `key=value` fields
- Includes context: yes — HTTP method + bounded origin only
- Log levels: `ERROR` at the outbound rejection boundary
- Large/sensitive data: path, query, fragment, credentials, and segment values
  are omitted from the ERROR line (same helper as
  `template_integer_conversion_failed`)

### Related existing logs (unchanged)

MCP / collection callers still surface the rejection through the existing
`ExecutionError` → MCP structured tool result envelope (`error: true`,
`error_category=template`, actionable `error_message` / detail). Upstream
`request_execution_failed` may also fire when `RequestService` catches the
error; that path continues to log the **template** URL, not the rendered path.

## Metrics Implementation (if applicable)

### Performance Metrics

No new performance metrics:
- **Response time**: N/A for a pre-dispatch reject (no network round-trip)
- **Throughput**: existing `track_request_sent(method)` still increments at the
  start of `send_request` before prepare (same timing as invalid `to_int`)
- **Error rate**: when rejection flows through `RequestService`, existing
  `track_request_error(ErrorCategory.TEMPLATE)` records the failure category.
  Direct `_prepare_request_kwargs` unit paths do not record metrics.

### Business Metrics

None. Dot-segment rejection is a security/validation outcome, not a business
conversion event. Labelling by rejected segment would be unsafe and noisy.

### System Health Metrics

None. The change adds no new component, worker, or health state.

## Monitoring Integration

Integration with monitoring systems:
- [x] Prometheus metrics — existing request-error / MCP counters cover
  production reject paths through `RequestService` / MCP (no new series)
- [ ] Grafana dashboards — no task-specific dashboard
- [ ] Alerting rules — occasional agent misuse is observable via ERROR logs;
  not a service-health alert by itself
- [x] Log aggregation — structured `dot_path_segment_rejected` event is
  available when application logs are collected
- [x] CI test log guardrails — prefix registered in
  `tests/expected_log_allowlist.yaml`; baseline raised for intentional ERROR
  emissions from Step 3/4/6 rejection tests

## Validation Results

Validation results:
- [x] Logs are correctly formatted — `dot_path_segment_rejected method=… url=…`
- [x] Metrics are collected correctly — N/A for new metrics; documented reuse of
  `track_request_error(TEMPLATE)`
- [x] Logging works in error scenarios — assertLogs regressions in
  `TestHTTPClientDotPathSegmentRejection`
- [x] Large data structures are not logged — origin-only URL; path/segment
  omitted
- [x] Caplog / allowlist contract — C1 via assertLogs tests; C2 via allowlist
  rule `pypost.core.http_client` / `dot_path_segment_rejected`
- [x] Focused tests via `make test` (see roadmap Step 6 sub-items)

## Notes

- Shared helper `_template_error_log_url` is intentional parity with
  `template_integer_conversion_failed` (PYPOST-1037).
- Percent-encoded lookalikes (`%2e`) remain out of scope; no observability for
  that class until a follow-up implements rejection.
- Blank-segment rejection (PYPOST-1332) should reuse this checkpoint and the
  same origin-bounded ERROR pattern when implemented.
