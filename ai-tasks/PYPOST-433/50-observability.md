# PYPOST-433: Observability

## Summary

Test-only task — no new log events or metrics in production code.

## Covered log events (asserted in new tests)

| Event | Location | Test |
| --- | --- | --- |
| `environment_copied` | `EnvironmentListWidget._duplicate_environment_at_row` | `test_duplicate_environment_logs_copied_event` |

## Existing events (unchanged, still covered by prior tests)

| Event | Location |
| --- | --- |
| `environment_deleted` | `EnvironmentListWidget.delete_environment` |
| `environment_renamed` | `EnvironmentListWidget` rename paths |
| `env_hidden_flag_changed` | `EnvironmentVariablesWidget._on_hidden_toggled` |
| `env_variable_deleted` | `EnvironmentVariablesWidget.delete_variable_at_row` |
| `env_variable_moved` | `EnvironmentVariablesWidget.move_variable_at_row` |

## Checklist

- [x] No production logging changes
- [x] Copy success path log verified via `caplog`
- [x] Hidden key masking in logs unchanged (existing tests)
