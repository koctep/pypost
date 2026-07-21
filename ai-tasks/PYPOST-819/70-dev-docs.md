# PYPOST-819: Dev Docs Update

## Changes

Updated `doc/dev/request_actions.md` Testing section:

- Added `test_close_last_request_tab_focuses_replacement_not_plus` to the plus/tab test
  table (closing the last request tab creates a blank replacement via `add_new_tab` and
  focuses it, not `+`).

## Validation

- [x] Docs match the new test in `tests/test_tabs_presenter.py`
- [x] Existing plus-tab `make test` command remains valid for related coverage
- [x] No production Architecture/Troubleshooting changes needed
