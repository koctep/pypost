# PYPOST-825: Dev Docs Update

## Changes

`doc/dev/request_actions.md` already documents the post-close navigable reselect from
PYPOST-824 (plus-placeholder section and troubleshooting “Closing a request tab leaves
focus on `+`”), including the regression test
`test_close_rightmost_of_*_does_not_land_on_plus`.

For this ticket:

- [x] Confirmed existing docs match production `close_tab` behavior
- [x] Added a short verification note that PYPOST-825 (two-tab rightmost) is covered by
  the same documented fix / tests (sibling of PYPOST-824)

No separate Architecture doc or new `doc/dev/` file was required.

## Validation

- [x] Docs match production `close_tab` behavior (PYPOST-824 content still accurate)
- [x] Land-on-plus tests listed in the existing test / troubleshooting tables
- [x] Verification note only — no duplicate long-form rewrite of the PYPOST-824 docs
