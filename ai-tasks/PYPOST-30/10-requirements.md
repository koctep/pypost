# PYPOST-30: Fix AttributeError: 'MainWindow' object has no attribute 'on_env_update'

## Goals

Fix the runtime error that occurs when updating environment variables from request scripts by
implementing the missing `on_env_update` method in the application main window.

## User Stories

- As a developer, I want environment variable updates from scripts to work correctly so request
  automation runs without failures.
- As a user, I don't want to see an error dialog when running requests that modify the
  environment.

## Acceptance Criteria

- No `AttributeError` when running a script that updates environment variables.
- Environment variables are correctly updated in the currently selected environment.
- Updated variables are shown in the UI (if management dialog is open or tabs are refreshed).
- Changes are saved to the environments file.

## Task Description

When executing a request, if the script tries to update environment variables (e.g. via
`pypost.env.set`), `RequestWorker` emits the `env_update` signal. This signal is connected to
`self.on_env_update` in `MainWindow` (file `pypost/ui/main_window.py`). However, this method is not
implemented in the `MainWindow` class, causing the application to crash with:
`AttributeError: 'MainWindow' object has no attribute 'on_env_update'`.

This method must be implemented.

## Q&A

- **Q:** How should the method behave if no environment is selected (No Environment)?
- **A:** If no environment is selected, variable updates should be ignored or a warning shown (in
  current implementation `RequestWorker` passes variables, but `MainWindow` must decide where to
  write them). It makes sense to write only to the active environment. If there is none — do
  nothing or notify the user. *Decision:* If no environment is selected, do nothing (safe option),
  as scripts usually assume context exists.

