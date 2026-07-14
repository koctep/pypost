# PYPOST-798: Dev Docs Update

## Changes

Updated `doc/dev/request_actions.md` Testing section:

- Documented dual click-path test strategy (primary `QTest.mouseClick` + fallback
  `tabBarClicked.emit`).
- Added three new tests to the plus-tab test table.
- Kept existing `make test` command for targeted plus-tab runs.

## Validation

- [x] Docs match new tests in `test_tab_header.py` and `test_tabs_presenter.py`
- [x] Primary and fallback paths both documented in Testing section
- [x] No changes to production Architecture/Troubleshooting sections (already correct from PYPOST-797)

## Worklog

role: execution, step: 7, step_name: Dev Docs, tokens_used: 450
