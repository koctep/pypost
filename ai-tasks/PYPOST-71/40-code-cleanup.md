# PYPOST-71 — Code Cleanup

## Summary

Removed 8-line `self.sender()` tab scan; handler signature now documents intent.

## Checklist

- [x] No dead imports or unused variables after loop removal.
- [x] Closure uses `t=tab` default binding (project convention from PYPOST-43 review).
- [x] Handler parameter named `sender_tab` (matches existing body references).
- [x] Test class follows `TestTabsPresenter*` naming in `test_tabs_presenter.py`.
