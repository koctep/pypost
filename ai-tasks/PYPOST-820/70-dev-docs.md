# PYPOST-820: Dev Docs Update

## Changes

Updated `doc/dev/request_actions.md` Testing section:

- Added `test_close_middle_of_three_tabs_focuses_remaining_request_tab` to the plus/tab test
  table (close middle of three keeps focus on a remaining request tab, not `+`).

## Validation

- [x] Docs match the new test in `tests/test_tabs_presenter.py`
- [x] Existing plus-tab `make test` command remains valid for related coverage
- [x] No production Architecture/Troubleshooting changes needed
