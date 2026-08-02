# PYPOST-1038: Observability Review

## Decision

No production observability change is required.  PYPOST-1038 uses the existing
template-rendering and HTTP failure telemetry without adding identifier values,
per-tool labels, or other high-cardinality dimensions.

## Existing signals

| Outcome | Existing signal | Safety property |
| --- | --- | --- |
| Valid decimal string or native integer renders | `template_expression_render_attempts_total{render_path="http",outcome="success"}` and the existing render-duration histogram | Fixed, bounded labels; identifier is not a label. |
| Invalid `to_int` input is rejected before dispatch | `template_expression_render_attempts_total{render_path="http",outcome="render_error"}` plus `template_integer_conversion_failed` at ERROR | The HTTP log contains only method and a bounded, sanitized origin; it excludes the identifier, credentials, headers, body, path, query, and fragment. |
| Malformed or wrong-arity expression is rejected | Existing `validation_error` render-attempt outcome and `template_expression_validation_failures_total` | Labels are the existing bounded render path, validation code, and allow-listed function name. |

The generic request metrics still record normal HTTP dispatches.  Invalid
identifiers do not reach that dispatch path, which is the desired fail-closed
behavior rather than a missing signal.

## Evidence

- `tests/test_mcp_server_integration.py::TestMCPServerIntegration::test_jira_numeric_path_identifiers_accept_decimal_strings_and_native_integers`
  verifies every affected Jira path for both accepted forms.
- `tests/test_mcp_server_integration.py::TestMCPServerIntegration::test_jira_non_integral_identifier_never_dispatches_to_http`
  verifies rejected string and float inputs make no outbound call.
- `tests/test_http_client.py` verifies the ERROR event and its redaction/bounded
  origin behavior; `tests/test_template_service.py` verifies native-integer
  acceptance and bool/float rejection.
- Focused Step 6 validation: **5 passed** (2026-08-03).

## Independent review

Independent Step 6 review: **PASS**.  It confirmed that existing success,
validation-error, and render-error metrics cover the change; no new telemetry
is warranted and the implementation adds no dynamic metric label or sensitive
log field.

## Documentation impact

No observability documentation change is required: `doc/prometheus_monitoring.md`
and `doc/dev/template_expression_functions.md` already document the metric and
safe HTTP error event used here.  The broader `to_int` usage wording is handled
by the separate Step 8 development-documentation pass.
