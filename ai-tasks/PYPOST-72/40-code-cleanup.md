# PYPOST-72 — Code Cleanup

## Summary

Extracted `_index_of_tab` and `_request_tab_before_dialog` to avoid duplicated tab-resolution
logic in save-new and save-as handlers.

## Checklist

- [x] No dead imports or unused variables.
- [x] Helper names describe intent (tab before dialog, index lookup).
- [x] Line length within 100 characters.
- [x] Test class follows `TestTabsPresenter*` naming.
