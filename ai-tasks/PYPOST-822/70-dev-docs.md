# PYPOST-822: Dev Docs Update

## Changes

Updated `doc/dev/request_actions.md` Testing section:

- Added `test_next_previous_tab_hotkeys_keep_focus_on_request_tabs` to the plus/tab test
  table (next/previous hotkey map keeps focus on request tabs, not `+`).

## Validation

- [x] Docs match the new test in `tests/test_tabs_presenter.py`
- [x] Note on `register_hotkey` + `triggered.emit` (vs flaky offscreen key delivery) lives in
  the test docstring and architecture artifact
- [x] No production Architecture/Troubleshooting changes needed
