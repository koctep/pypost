# PYPOST-489: Architecture

## Approach

Extend `tests/test_env_persistence_e2e.py` with one focused acceptance test. Reuse existing
patterns from the same file (temp storage, `StorageManager` round-trip) and from
`tests/test_env_dialog.py` (caplog at INFO, `_get_hidden_checkbox` toggle).

## Test flow

1. Save `Environment` with a plain variable to temp storage.
2. `load_environments()` — persistence round-trip.
3. `EnvironmentDialog(reloaded)` — no `log_hidden_key_names` (default `False`).
4. Select environment, toggle hidden checkbox ON under `caplog.at_level(logging.INFO)`.
5. Assert `env_hidden_flag_changed` with `key=********`, `env_name=Dev`, `hidden=True`.
6. Assert variable key and value do not appear in log messages.

## Files

| File | Change |
| --- | --- |
| `tests/test_env_persistence_e2e.py` | Add `test_default_masked_toggle_log_after_persistence_round_trip` |

No production changes expected.

## Out of scope

- Presenter-based restart flows (covered by sibling tests; logging is dialog-constructor concern).
- Settings integration (PYPOST-490).
