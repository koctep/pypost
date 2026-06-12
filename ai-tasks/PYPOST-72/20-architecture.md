# PYPOST-72 — Architecture

## Change Surface

| File | Change |
|------|--------|
| `pypost/ui/presenters/tabs_presenter.py` | Capture tab before orchestrator; apply save result to captured tab |
| `tests/test_tabs_presenter.py` | Regression tests for dialog-time tab switch |

## Design

### Helpers

- `_index_of_tab(tab)` — widget index for header label updates.
- `_request_tab_before_dialog(source_tab, tab_index)` — prefer explicit sender tab; fall back
  to widget at index captured before dialog.

### Save-new (`CREATED_NEW`)

1. `source_tab = _find_tab_for_sender()` and `tab_index_before = currentIndex()` **before**
   `_save_orchestrator.save_request`.
2. On success, resolve `target_tab = _request_tab_before_dialog(...)`.
3. Update label via `_index_of_tab(target_tab)`; apply baseline via
   `_apply_save_result_to_tab(target_tab, ...)`.

### Save-as (`SAVE_AS`)

Same capture/apply pattern as save-new.

### Overwrite path

Unchanged — already uses `source_tab` from pre-dialog capture.

## Test Strategy

Patch `SaveRequestDialog.exec` to switch `currentIndex` mid-dialog; patch
`_find_tab_for_sender` to return known source tab; assert source tab updated, sibling tab
unchanged.
