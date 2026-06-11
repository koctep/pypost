# PYPOST-478: Observability

## Summary

Observability behaviour for the new-variable creation flow is **unchanged**. Metrics and DEBUG
logging remain in `EnvPresenter._is_valid_variable_name`, which wraps the shared validator.

## Logging

| Event | Level | Location | Message pattern |
| --- | --- | --- | --- |
| Validation attempt (valid) | DEBUG | `EnvPresenter._is_valid_variable_name` | `variable_name_validation_attempt name=%s valid=True error=` |
| Validation attempt (invalid) | DEBUG | `EnvPresenter._is_valid_variable_name` | `variable_name_validation_attempt name=%s valid=False error=%s` |
| Variable set success | INFO | `EnvPresenter.handle_variable_set_request` | `variable_set_in_env env_id=%s ...` (unchanged) |

## Metrics

| Metric | Labels | When emitted |
| --- | --- | --- |
| `gui_variable_validation_total` | `result=valid\|invalid` | After each validation in presenter wrapper |
| `gui_variable_validation_failures_total` | `reason=empty\|starts_with_digit\|invalid_chars` | On invalid names only |

## Core module

`validate_variable_name` performs **no** logging or metrics — keeps the helper usable from tests
and non-UI callers without side effects.
