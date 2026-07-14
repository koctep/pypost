# PYPOST-741: Observability

## Logging changes

All four `HTTPClient` ERROR paths now emit sanitized resolved URLs:

| Event | Prefix | URL field |
| --- | --- | --- |
| Timeout | `Request timed out` | `_error_log_url(resolved)` |
| Connection | `Connection failed` | `_error_log_url(resolved)` |
| Transport | `Request failed` | `_error_log_url(resolved)` |
| YAML conversion | `yaml_to_json_conversion_failed` | `_error_log_url(resolved)` |

Host and path remain for correlation; query tokens and literal secrets are redacted to `***`.

## Metrics

No new metrics. Existing `yaml_to_json_conversion_failed_total` unchanged.
