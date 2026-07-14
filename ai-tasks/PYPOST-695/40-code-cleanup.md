# PYPOST-695: Code Cleanup

## Changes

- Removed redundant inline construction of three services from `MainWindow.__init__`.
- Tests that previously patched `StorageManager`/`RequestManager` at `main_window` now inject
  mocks via constructor where asserting real storage behavior.
- No dead imports or duplicate wiring left in `MainWindow`.

## Verification

- `make analyze` — no new lint issues in touched files.
