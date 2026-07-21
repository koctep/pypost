# PYPOST-824: Dev Docs Update

## Changes

Updated `doc/dev/request_actions.md`:

- Plus-placeholder section: document that `TabsPresenter.close_tab` reselects via
  `navigable_tab_indices()` when Qt `removeTab` leaves current on trailing `+`.
- Troubleshooting: new subsection “Closing a request tab leaves focus on `+`” with
  root cause, fix pointer (PYPOST-824), and regression test names.

## Validation

- [x] Docs match production `close_tab` behavior
- [x] Existing plus/tab test table already lists the land-on-plus tests
- [x] No separate Architecture doc needed beyond this update
