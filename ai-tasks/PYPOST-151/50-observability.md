# PYPOST-151: Observability

## Logging

On validation failure, `SettingsDialog` logs:

```
bind_address_settings_validation_failed field=<label> reason=<empty|invalid_format|out_of_range>
```

Level: **WARNING** (same pattern as `retryable_codes_settings_validation_failed`).

## Metrics

No new metrics — settings validation is a rare user-path event.

## Rationale

Structured `field` and `reason` support log filtering without exposing user-entered host
strings in multiple log lines (single WARNING per failed save attempt).
