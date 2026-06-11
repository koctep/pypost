# PYPOST-473: Dev Docs

## Updated

- `doc/dev/variable_validation.md` — Observability section now states DEBUG logs are emitted
  for **failed** validation attempts only; metrics still count all attempts.

## Unchanged

- Rule source, UI flow, examples, and test file references remain accurate.

## Verification

- Doc policy matches `EnvPresenter._is_valid_variable_name` implementation.
- Presenter tests document expected logging behaviour.
