# PYPOST-496: Observability

## Summary

Refactor only — no new log events or metrics.

## Preserved log events

| Event | Location |
| --- | --- |
| `environment_deleted` | `EnvironmentListWidget.delete_environment` |
| `environment_renamed` | `EnvironmentListWidget` rename paths |
| `environment_copied` | `EnvironmentListWidget._duplicate_environment_at_row` |
| `env_hidden_flag_changed` | `EnvironmentVariablesWidget._on_hidden_toggled` |
| `env_variable_deleted` | `EnvironmentVariablesWidget.delete_variable_at_row` |
| `env_variable_moved` | `EnvironmentVariablesWidget.move_variable_at_row` |

## Hidden key formatting

`HiddenToggleLogPolicy.format_key_name` usage unchanged; `log_hidden_key_names` flows from
`EnvironmentDialog` constructor into `EnvironmentVariablesWidget`.

## Checklist

- [x] No log message format changes
- [x] No new PII exposure paths introduced
