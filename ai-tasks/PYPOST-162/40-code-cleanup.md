# PYPOST-162 — Code Cleanup

## Summary

Removed `_find_tab_for_sender` (8 lines) and `_request_tab_before_dialog` (7 lines). Save handlers
now mirror the send-handler pattern from PYPOST-71.

## Checklist

- [x] No dead imports or unused variables after helper removal.
- [x] Closure uses `t=tab` default binding (project convention).
- [x] Handler parameter named `source_tab` (matches save orchestrator usage).
- [x] Test class follows `TestTabsPresenter*` naming in `test_tabs_presenter.py`.
