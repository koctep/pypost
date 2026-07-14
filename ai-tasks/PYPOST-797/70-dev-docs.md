# PYPOST-797: Dev Docs Update

## Changes

Updated `doc/dev/request_actions.md`:

- **Architecture** — `RequestTabHeader` documents dual click paths: `plus_btn.clicked` (primary)
  and `tabBarClicked` via `_on_tab_bar_clicked` (fallback for plus-tab chrome).
- **New-tab flow** — Step list includes header emission before presenter handling.
- **Plus placeholder tab** — Explains why `plus_btn.clicked` is required when the `+` control
  is embedded via `QTabBar.setTabButton` (Qt does not emit `tabBarClicked` for child widget
  clicks).
- **Troubleshooting** — Refreshed "`Ctrl+N` works but `+` click does nothing" to check
  `plus_btn.clicked` wiring and embedded button presence first.
- **Testing** — Added plus-tab test table and `make test` command using real
  `QTest.mouseClick` on the embedded button.

## Validation

- [x] Docs match implemented code in `RequestTabHeader.ensure_plus_tab()` and
      `TabsPresenter.handle_new_tab()`
- [x] Primary path (`plus_btn.clicked`) and fallback (`tabBarClicked`) both documented
- [x] Troubleshooting reflects PYPOST-797 root cause (missing `clicked` wiring after
      PYPOST-792 layout restore)
- [x] Test documentation references `QTest.mouseClick` pattern from Step 3

## Worklog

role: execution, step: 7, step_name: Dev Docs, tokens_used: 850
