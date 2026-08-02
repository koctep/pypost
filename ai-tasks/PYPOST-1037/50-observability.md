# PYPOST-1037: Observability Implementation

## Observability Decision

PYPOST-1037 adds an allow-listed `to_int(...)` template expression and a
narrow fail-closed HTTP preparation path for invalid integer conversion.  The
critical operational event is an HTTP request that is intentionally blocked
before `session.request` because conversion failed. The existing template
observability and the implemented safe HTTP ERROR event already cover that
event with bounded context, so no new metric schema is warranted.

## Logging Implementation

### Added Logs

The implementation includes the required structured, error-level HTTP event:

- **ERR**: `pypost.core.http_client` emits
  `template_integer_conversion_failed` when strict conversion rejects an
  outbound URL, header, parameter, or body field.  It includes only the HTTP
  method and a bounded, sanitized request origin (scheme, hostname, and a
  valid explicit port only). It omits user info, path, query, and fragment;
  malformed URLs use a fixed safe placeholder, and output is capped at 512
  characters. It does not include the failed value, headers, parameters, or
  request body.

The existing `TemplateService` event remains active before that boundary:

- **WARNING**: `template_render_fallback_to_original` records the render path,
  exception type, and placeholder count.  It contains no rendered value or
  template variable map.

No **EMERG**, **ALERT**, **CRIT**, **NOTICE**, **INFO**, or **DEBUG** event is
needed for a rejected user input.  A successful conversion is already covered
by the normal successful template-render event and should not create a noisy
per-request log.

### Log Structure

- Structured logs: yes, stable event names with named context fields.
- Includes context: yes — request method, sanitized URL, render path,
  exception type, and token count as appropriate.
- Log levels: `ERROR` at the outbound rejection boundary and `WARNING` for the
  existing render fallback.
- Large/sensitive data: neither log contains a request body, parameter map,
  header values, or failed conversion input.

## Metrics Implementation

No new metric is necessary.  Existing cross-backend template metrics provide
the required signal without introducing a new function-name or value label:

- **Error rate:** `template_expression_render_attempts_total` increments with
  `render_path="http", outcome="render_error"` for a runtime invalid
  `to_int` value; validation failures continue to use
  `outcome="validation_error"`.
- **Validation diagnosis:**
  `template_expression_validation_failures_total` records the validation code
  and function name for malformed or wrong-arity calls that fail before Jinja
  rendering.
- **Performance:** `template_expression_render_duration_seconds` records the
  Jinja render duration after expression validation by `render_path`, including
  the valid HTTP render phase. Malformed or wrong-arity calls fail during
  validation and are not included in this histogram.

`MetricsRegistry` and the OpenTelemetry implementation already expose the
same metric names and labels.  A distinct `to_int` counter would duplicate
these bounded signals and increase label/cardinality surface without an
operational decision that needs it.

### Business Metrics

None.  A conversion failure is a request-validation result, not a business
event, and recording values would be unsafe.

### System Health Metrics

None.  This change adds no component, worker, resource consumer, or health
state.

## Monitoring Integration

- [x] Prometheus metrics — existing template counters and histogram are
  exported through the existing metrics server.
- [x] OpenTelemetry metrics — existing tracker mirrors the same bounded
  template metric names and dimensions.
- [ ] Grafana dashboards — no task-specific dashboard threshold is justified.
- [ ] Alerting rules — invalid caller input is observable but is not by itself
  a service-health alert.
- [x] Log aggregation — existing structured application logs carry the safe
  failure event when aggregation is configured.

## Validation Results

- [x] Reviewed strict conversion behavior in URL, header, parameter, and JSON
  body preparation; each failure becomes `ExecutionError(TEMPLATE)` before
  `session.request`.
- [x] Added a focused regression assertion that an invalid runtime conversion
  emits `template_integer_conversion_failed`, omits the rejected value, and
  records the existing HTTP `render_error` metric.
- [x] Error URL context retains only a bounded origin (scheme, hostname, and
  valid explicit port). It omits user info, path, query, and fragment —
  including static non-token sensitive values — and uses a fixed placeholder
  for malformed URLs.
- [x] Focused template/HTTP suite passed:
  `PYTEST_ARGS='tests/test_template_service.py tests/test_http_client.py' make test`
  (120 passed).
- [x] `make lint` and `git diff --check` passed.
- [x] Large data structures are not logged; neither new nor existing relevant
  event carries bodies, headers, params, or raw template variables.

## Notes

The metrics deliberately distinguish runtime conversion errors from validation
errors while sharing the existing template namespace.  If operational data
later shows a sustained conversion-failure rate, alerting can be configured
from the existing HTTP-path render-error metric without a code change.
