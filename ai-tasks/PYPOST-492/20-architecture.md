# PYPOST-492: Architecture

## Research

- **Source**: `ai-tasks/PYPOST-448/60-tech-debt.md` — SettingsDialog checkbox uses
  `addRow("", checkbox)` with inline label; recommends Security / Logging section.
- **Current layout** (`settings_dialog.py`): general prefs → encryption → retry → webhooks;
  `log_hidden_key_names` inserted after confirm-overwrite checkbox.
- **Persistence**: `AppSettings` fields unchanged; `accept()` already maps all three controls.

## Implementation plan

1. Add `_make_section_header(title)` helper returning a bold `QLabel` (module-level, reused
   pattern similar to `hotkeys_dialog.py` title styling).
2. Remove early `addRow` for `log_hidden_key_names_check` (after confirm overwrite).
3. After retry policy rows, add:
   - Section header "Security / Logging"
   - `log_hidden_key_names_check` (`addRow("", checkbox)` — label on widget)
   - Alert webhook URL and auth header rows (unchanged labels)
4. Store `security_logging_section_label` on dialog for tests.
5. Extend `tests/test_settings_dialog.py` with order and header assertions.

## Module responsibilities

| Module | Change |
| ------ | ------ |
| `pypost/ui/dialogs/settings_dialog.py` | Layout reorder + section header helper |
| `tests/test_settings_dialog.py` | Layout grouping tests |

## Testing strategy

- `TestSettingsDialogSecurityLoggingSection`: header text, form index ordering.
- Re-run `TestSettingsDialogLogHiddenKeyNames` and full `test_settings_dialog.py`.

## Q&A

| Question | Answer |
| -------- | ------ |
| New widget types? | No; QLabel header only. |
| Tab order | Follows new visual order (retry → section → checkbox → webhooks). |
