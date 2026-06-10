# PYPOST-481: Technical Debt Analysis

## Shortcuts Taken

No significant shortcuts. Settings expose policy only; key material remains in environment
variables per security requirements.

## Code Quality Issues

- `SettingsDialog.accept()` manually lists every `AppSettings` field when constructing the saved
  model. Adding future settings still requires updating this method.
  Jira: existing pattern; no new ticket filed.
- `encryption_config.build_key_provider()` supports only `"environment"`; additional providers
  (keyring, vault) are deferred to PYPOST-483 / PYPOST-487 from PYPOST-447 debt.

## Missing Tests

- No automated UI test for `MainWindow.open_settings()` applying encryption policy to
  `StorageManager` end-to-end (covered indirectly via storage + dialog unit tests).
  Jira: [PYPOST-499](https://pypost.atlassian.net/browse/PYPOST-499)
- No test for unsupported key source combo entries in UI (only one source enabled today).
  Low priority; deferred until additional key sources ship (PYPOST-483).

## Performance Concerns

None introduced. Encryption work remains on environment save/load paths as in PYPOST-447.

## Follow-up Tasks

- Add additional key provider strategies (keyring, external secret store) and enable UI options.
  Jira: [PYPOST-483](https://pypost.atlassian.net/browse/PYPOST-483) (blocker: provider
  implementations)
- Evaluate migration tooling when togg encryption settings togg existing plain-text hidden values.
  Jira: [PYPOST-487](https://pypost.atlassian.net/browse/PYPOST-487) (blocker: key provider
  strategy work)
- Extract environment serialization/encryption from `StorageManager` into dedicated adapter.
  Jira: [PYPOST-482](https://pypost.atlassian.net/browse/PYPOST-482) (non-blocker)
