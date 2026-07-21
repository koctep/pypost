# PYPOST-826: Dev Docs Update

## Changes

Core post-close focus documentation (navigable reselect after `removeTab`, plus
troubleshooting) was already written under **PYPOST-824** in
`doc/dev/request_actions.md`.

**Unique PYPOST-826 doc touch:** extended the troubleshooting bullet so close-current /
`handle_close_tab` verification is attributed to this ticket (alongside PYPOST-824 fix
ownership and PYPOST-825’s two-tab rightmost verification).

## PYPOST-826 note

- Entry point: close-current / `handle_close_tab` → `close_tab`.
- Production fix owner: PYPOST-824 (`TabsPresenter.close_tab`).
- Verification: `test_handle_close_tab_closes_current` PASSED after the PYPOST-824 fix.

## Validation

- [x] Docs match production `close_tab` behavior (PYPOST-824)
- [x] Unique PYPOST-826 verification note present in troubleshooting
- [x] Regression test name listed in `doc/dev/request_actions.md`
