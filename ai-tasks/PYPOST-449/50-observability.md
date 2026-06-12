# PYPOST-449: Observability (STEP 5)

## Scope

Refactor-only task. No new log lines, metrics, or signals.

## Existing observability (unchanged)

| Event | Logger | Trigger |
| --- | --- | --- |
| `env_hidden_flag_changed` | `environment_variables_widget` | Hidden checkbox toggle |
| `env_variable_deleted` | `environment_variables_widget` | Context-menu delete |
| `env_variable_moved` | `environment_variables_widget` | Context-menu move up/down |

Hidden-key name redaction still flows through `HiddenToggleLogPolicy` when
`log_hidden_key_names=False`.

## Verification

```bash
python3 -m pytest tests/test_env_dialog.py -k "hidden_toggle_logs or delete_variable_logs or move_variable_logs" -q
```

No observability regressions expected — helper extraction does not alter log call sites.
