# PYPOST-473: Observability

## Summary

Tuned validation DEBUG logging to **failures only**. Metrics and INFO logs unchanged.

## Logging (after)

| Event | Level | Location | Message pattern |
| --- | --- | --- | --- |
| Validation success | — | `EnvPresenter._is_valid_variable_name` | *(no log — use metrics)* |
| Validation failure | DEBUG | `EnvPresenter._is_valid_variable_name` | `variable_name_validation_attempt name=%s valid=False error=%s` |
| Variable set success | INFO | `EnvPresenter.handle_variable_set_request` | `variable_set_in_env env_id=%s ...` (unchanged) |

## Metrics (unchanged)

| Metric | Labels | When emitted |
| --- | --- | --- |
| `gui_variable_validation_total` | `result=valid\|invalid` | After each validation |
| `gui_variable_validation_failures_total` | `reason=empty\|starts_with_digit\|invalid_chars` | On invalid names only |

## Core module

`validate_variable_name` performs no logging — unchanged.

## Tests

- `test_valid_variable_name_does_not_emit_debug_log`
- `test_invalid_variable_name_emits_debug_log`
