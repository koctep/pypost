# PYPOST-448: Technical Debt Analysis

## Shortcuts Taken

- Logging policy is snapshotted at `EnvironmentDialog` construction time. A user who changes
  the setting while the environment manager is already open must close and reopen the dialog
  for the new policy to apply. This matches the approved architecture and requirements
  (subsequent events only) but is a deliberate UX limitation, not live hot-reload.
  - Jira: _none_ (accepted by design)
- No INFO log was added when the user toggles `log_hidden_key_names` in Settings. Policy
  change is silent in logs; only the checkbox state in `settings.json` records the preference.
  - Jira: _none_ (low impact)

## Code Quality Issues

- `pypost/core/hidden_toggle_log_policy.py` imports `HIDDEN_MASK` from
  `pypost/ui/widgets/mixins.py`, creating a core → UI layer dependency. For a one-field
  policy this is acceptable short-term, but the mask constant belongs in a shared module
  (e.g. `pypost/core/constants.py` or next to `SensitiveDataMaskingPolicy`).
  - Jira: [PYPOST-491](https://pypost.atlassian.net/browse/PYPOST-491) (Medium, Debt)
- `SettingsDialog` places the new checkbox with `addRow("", checkbox)` — label text lives on
  the `QCheckBox` itself. Consistent with some existing rows but differs from labeled spinbox
  rows; a dedicated "Security / Logging" section header would improve discoverability.
  - Jira: [PYPOST-492](https://pypost.atlassian.net/browse/PYPOST-492) (Low, Debt)

## Missing Tests

- No end-to-end test covers Settings save → `MainWindow.apply_settings` →
  `EnvPresenter._open_env_manager` → masked toggle log. Coverage is split across
  `test_settings_dialog`, `test_env_presenter.apply_settings`, and `test_env_dialog` caplog
  tests but not wired in one flow.
  - Jira: [PYPOST-490](https://pypost.atlassian.net/browse/PYPOST-490) (High, Debt)
- `tests/test_env_persistence_e2e.py` constructs `EnvironmentDialog` without
  `log_hidden_key_names`; it does not assert default masked logging after persistence round-
  trip.
  - Jira: [PYPOST-489](https://pypost.atlassian.net/browse/PYPOST-489) (Low, Debt)
- No test verifies `env_name` is still logged when key is redacted (only full message string
  asserted in caplog tests).
  - Jira: _none_ (covered implicitly by existing caplog assertions)
- Full project regression suite was not run in this task scope; only 53 targeted tests
  executed.
  - Jira: _none_ (standard pre-merge practice)

## Performance Concerns

- None. `HiddenToggleLogPolicy.format_key_name` is O(1) string return on a low-frequency UI
  event. No metrics or async paths added.

## Deviations from Architecture

- None. Implementation matches `20-architecture.md`: policy module, `AppSettings` field,
  Settings checkbox, constructor injection, `EnvPresenter.apply_settings`, caplog tests.

## Documentation Debt

- ~~`doc/dev/hidden_variables.md` outdated (PYPOST-437 text).~~ **Resolved in STEP 7**
  (PYPOST-448 `70-dev-docs.md`, `doc/dev/hidden_variables.md` updated).
  - Jira: [PYPOST-488](https://pypost.atlassian.net/browse/PYPOST-488) (High, Debt) — close
    when verified

## Follow-up Tasks

- [PYPOST-488](https://pypost.atlassian.net/browse/PYPOST-488) (High, Debt): Document
  `log_hidden_key_names` and breaking default in `doc/dev/hidden_variables.md`.
- [PYPOST-490](https://pypost.atlassian.net/browse/PYPOST-490) (High, Debt): Integration test
  for settings → apply_settings → env dialog → masked toggle log flow.
- [PYPOST-491](https://pypost.atlassian.net/browse/PYPOST-491) (Medium, Debt): Extract
  `HIDDEN_MASK` to shared constants module (remove core → UI dependency).
- [PYPOST-492](https://pypost.atlassian.net/browse/PYPOST-492) (Low, Debt): Group security/
  logging settings section in SettingsDialog.
- [PYPOST-489](https://pypost.atlassian.net/browse/PYPOST-489) (Low, Debt): Extend env
  persistence e2e tests for default masked toggle logging.

All tickets: type **Debt**, linked to [PYPOST-448](https://pypost.atlassian.net/browse/PYPOST-448)
via **Relates**.
