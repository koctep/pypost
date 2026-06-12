# PYPOST-72 — Dev Docs

## Updates

| Doc | Change |
|-----|--------|
| `doc/dev/request_actions.md` | Note tab capture before save dialog |

## Key Point

`TabsPresenter._handle_save_request` and `_handle_save_as_request` capture the originating
tab (or tab index) **before** the save orchestrator runs modal dialogs. Post-save UI updates
use that captured reference so a tab switch during the dialog cannot mis-apply labels or
persisted baselines.

## Test Reference

- `tests/test_tabs_presenter.py::TestTabsPresenterSaveTabBinding`
