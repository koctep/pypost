# PYPOST-27: Technical Debt Analysis

## Shortcuts Taken

- When implementing `on_env_update` we ignore updates if no environment is selected (`None`).
  Perhaps a warning to the user (in log or status bar) that the script tried to update a variable
  but context is missing would be useful. Currently this happens "silently".

## Code Quality Issues

- No significant code quality issues. Implementation is concise and uses existing methods
  (`on_env_changed`, `storage.save_environments`).

## Missing Tests

- No automated tests for `MainWindow` and `RequestWorker` interaction when updating variables.
  Testing was done manually (assumed).
- Add unit test for `on_env_update` method, mocking `env_selector` and `storage`.

## Performance Concerns

- Environment saving (`self.storage.save_environments`) happens synchronously on every variable
  update from script. If a script updates variables in a loop very frequently, this could cause
  UI freezes and excess disk load.
  - *Mitigation:* Consider adding debounce or saving only after script completion, not on every
    `env_update` signal. In current architecture `RequestWorker` emits `env_update` after script
    execution (if variables changed), so this should not be a mass issue if `RequestWorker`
    accumulates changes. *Check:* `RequestWorker.run` emits `env_update` once after execution. So
    no problem.

## Follow-up Tasks

- Add unit tests for `MainWindow` (UI test coverage may currently be low).
- Consider notifying the user if a script tries to write to an "empty" environment.

