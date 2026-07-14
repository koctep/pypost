# PYPOST-694: Code Cleanup

## Changes

- Removed redundant `patch("pypost.ui.main_window.HistoryManager")` from 10 test modules in
  favor of constructor injection — aligns tests with documented DI pattern.
- Added DEBUG `history_manager_source` logging consistent with `config_manager_source`.

## Verification

- `make check` — flake8 + full pytest suite.
