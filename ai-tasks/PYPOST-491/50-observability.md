# PYPOST-491: Observability

## Summary

No new logs, metrics, or tracing added. This is a structural refactor only.

## Existing observability (unchanged)

- `env_hidden_flag_changed` INFO events still use `HiddenToggleLogPolicy.format_key_name`.
- Default policy (`log_hidden_key_names=False`): `key=********` via `HIDDEN_MASK` from
  `pypost.core.constants`.
- Opt-in policy: readable variable key name.

## Validation

- `tests/test_hidden_toggle_log_policy.py` — policy unit tests
- `tests/test_settings_hidden_toggle_logging_e2e.py` — end-to-end toggle log journey
- `tests/test_env_dialog.py` — caplog assertions on toggle events

Mask token and log message shape are unchanged; only import path moved.
