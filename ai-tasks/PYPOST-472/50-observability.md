# PYPOST-472: Observability

## Impact

No observability changes. Empty-name failures now always flow through
`_is_valid_variable_name`, which records:

- `gui_variable_validation_total{result="invalid"}`
- `gui_variable_validation_failures_total{reason="empty"}`
- DEBUG log `variable_name_validation_attempt ... valid=False error=empty`

Previously, the inline empty check skipped metrics/logging for whitespace-only
input. Behaviour is now consistent with other validation failures.
