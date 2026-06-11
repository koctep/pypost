# PYPOST-492: Observability

## Assessment

Layout-only UI change. No new log statements, metrics, or alert paths.

## Existing touchpoints (unchanged)

| Component | Level | Event |
| --------- | ----- | ----- |
| `settings_dialog.accept` | WARNING | `retryable_codes_settings_validation_failed` |
| `main.py` | INFO | `alert_manager_created`, `settings_applied` |
| `alert_manager` | WARNING/DEBUG | `alert_emitted`, `alert_webhook_*` |

## Decision

No observability changes required for this debt item.
