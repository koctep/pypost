# PYPOST-818: Dev Docs Update

## Changes

Updated `doc/dev/request_actions.md` Testing section:

- Added `test_close_first_of_two_tabs_focuses_remaining_request_tab` to the plus/tab test
  table (close first of two keeps focus on remaining request tab, not `+`).

## Validation

- [x] Docs match the new test in `tests/test_tabs_presenter.py`
- [x] Existing plus-tab `make test` command remains valid for related coverage
- [x] No production Architecture/Troubleshooting changes needed

## Worklog

role: execution, step: 7, step_name: Dev Docs, tokens_used: 800
