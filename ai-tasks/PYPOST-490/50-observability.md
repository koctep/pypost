# PYPOST-490: Observability Implementation

Test-only task: document and validate existing observability from PYPOST-448. No new production
logs or metrics were added.

## Logging Implementation

### Existing Logs Under Test

The integration tests guard one pre-existing INFO event emitted when a user toggles a variable's
hidden flag in the environment manager:

| Field | Value |
| --- | --- |
| **Event** | `env_hidden_flag_changed` |
| **Level** | INFO |
| **Location** | `pypost/ui/dialogs/env_dialog.py` — hidden-checkbox toggle handler |
| **Logger** | `pypost.ui.dialogs.env_dialog` |
| **Message template** | `env_hidden_flag_changed env_name=%s key=%s hidden=%s` |

Key-name representation is delegated to `HiddenToggleLogPolicy.format_key_name()` in
`pypost/core/hidden_toggle_log_policy.py`:

- **Default policy** (`log_hidden_key_names=False`): `key=********` (`HIDDEN_MASK`).
- **Opt-in policy** (`log_hidden_key_names=True`): `key=<variable_name>` (readable key name).

Privacy constraints inherited from PYPOST-437 / PYPOST-448:

- `env_name` and `hidden` are always logged.
- Variable **values** are never logged.

Settings wiring (already in production, verified end-to-end by this task):

1. `SettingsDialog` captures `log_hidden_key_names` on `accept()`.
2. `MainWindow.apply_settings` forwards to `EnvPresenter.apply_settings`.
3. `EnvPresenter._open_env_manager` passes
   `log_hidden_key_names=self._settings.log_hidden_key_names` into `EnvironmentDialog`.

### Added Logs

None. This task adds acceptance coverage only; observability behavior was shipped in PYPOST-448.

### Log Structure

Log format used:

- Structured logs: yes (key=value fields in message template)
- Includes context: yes (`env_name`, `key`, `hidden`)
- Log levels: INFO (existing event only)

## Metrics Implementation (if applicable)

No metrics apply to this flow. Hidden-flag toggle logging is a low-frequency desktop UI event;
PYPOST-448 did not introduce counters, and this task does not add any.

### Performance Metrics

- Not added (N/A).

### Business Metrics

- Not added (N/A).

### System Health Metrics

- Not added (N/A).

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Alerting rules
- [ ] Log aggregation (ELK, Loki, etc.)

Desktop application logging only; no new integration for this test-debt task.

## Validation Results

Validation results:

- [x] Existing logs are correctly formatted (asserted via pytest `caplog` at INFO)
- [x] Metrics are collected correctly (N/A — no metrics for this event)
- [x] Logging works on the success path (toggle under patched `EnvironmentDialog.exec`)
- [x] Large data structures are not logged (variable values excluded by assertion)
- [x] No new observability required for this task

### Integration test coverage (`tests/test_settings_hidden_toggle_logging_e2e.py`)

**`test_default_masked_toggle_log_after_settings_apply`**

- Journey: Settings (default) → apply → env manager → toggle hidden.
- Asserts masked `key=********`, no readable `API_KEY`, no variable value leak.

**`test_readable_toggle_log_when_settings_opt_in`**

- Journey: Settings (opt-in) → apply → env manager → toggle hidden.
- Asserts readable `key=API_KEY`, `env_name` and `hidden` present, no value leak.

Both tests capture logs with pytest `caplog` at `logging.INFO` while toggling the hidden
checkbox inside a patched `EnvironmentDialog.exec`, exercising the real
`log_hidden_key_names=self._settings.log_hidden_key_names` constructor wiring from
`EnvPresenter._open_env_manager`.

### Relationship to existing observability tests

| Concern | Owner |
| --- | --- |
| `HiddenToggleLogPolicy.format_key_name` unit behavior | `tests/test_hidden_toggle_log_policy.py` |
| Toggle log with constructor arg passed directly | `tests/test_env_dialog.py` |
| Settings checkbox / `accept()` field | `tests/test_settings_dialog.py` |
| `apply_settings` reference swap | `tests/test_env_presenter.py` |
| Connected settings-to-toggle log flow | `test_settings_hidden_toggle_logging_e2e.py` |

## Gaps and Confirmations

**Confirmed — no new observability needed:**

- Requirements explicitly list observability changes (new logs, metrics, user docs) as out of
  scope.
- PYPOST-448 already defines the `env_hidden_flag_changed` contract and policy module.
- This task closes a **wiring** coverage gap, not a missing log event.

**Known limitations (not gaps for PYPOST-490):**

- Policy applies only when the environment manager is opened **after** saving Settings
  (PYPOST-448 accepted UX); not tested here.
- Environment persistence round-trip logging is PYPOST-489 scope.
- Delete/move variable log events are covered by separate tests (PYPOST-467).

## Notes

- Traceability: acceptance checks map to the missing-coverage item in
  [PYPOST-448 technical-debt analysis](ai-tasks/PYPOST-448/60-tech-debt.md).
- Parent observability design:
  [PYPOST-448/50-observability.md](ai-tasks/PYPOST-448/50-observability.md).
- Dev reference: `doc/dev/hidden_variables.md` documents the toggle log event and policy.
