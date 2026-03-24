# PYPOST-27: Technical Debt Analysis


## Shortcuts Taken

- When implementing `on_env_update` we ignore updates if no environment is selected (`None`). — [PYPOST-216](https://pypost.atlassian.net/browse/PYPOST-216)
  Perhaps a warning to the user (in log or status bar) that the script tried to update a variable
  but context is missing would be useful. Currently this happens "silently".

## Code Quality Issues

- **Small, idiomatic change** ([PYPOST-217](https://pypost.atlassian.net/browse/PYPOST-217)):
  No significant issues; implementation reuses `on_env_changed` and `storage.save_environments`.

## Missing Tests

- No automated tests for `MainWindow` and `RequestWorker` interaction when updating variables. — [PYPOST-218](https://pypost.atlassian.net/browse/PYPOST-218)
  Testing was done manually (assumed).
- Add unit test for `on_env_update` method, mocking `env_selector` and `storage`. — [PYPOST-219](https://pypost.atlassian.net/browse/PYPOST-219)

## Performance Concerns

- **Synchronous save on script env updates** ([PYPOST-220](https://pypost.atlassian.net/browse/PYPOST-220)):
  `self.storage.save_environments` runs on every variable update from a script; a tight loop could
  freeze the UI or hammer disk.
  - *Mitigation:* Debounce or save after script completion instead of every `env_update`. Today
    `RequestWorker` emits `env_update` once after execution when variables change, so bulk updates
    are unlikely.

## Follow-up Tasks

- Add unit tests for `MainWindow` (UI test coverage may currently be low). — [PYPOST-221](https://pypost.atlassian.net/browse/PYPOST-221)
- Consider notifying the user if a script tries to write to an "empty" environment. — [PYPOST-222](https://pypost.atlassian.net/browse/PYPOST-222)
