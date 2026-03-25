# Open Request in Isolated Tab

## Overview
Users can open multiple tabs for the same saved request. By default, the application's tree model serves as the single source of truth for a request. However, to prevent unintended sharing of volatile, unsaved UI state across multiple tabs editing the same request, PyPost offers an explicit "New tab" context menu action.

## Implementation Details
1. **Context Menu:** 
   The `CollectionsPresenter` provides a `New tab` option when right-clicking on a request node in the Collections sidebar. 
2. **Signal:** 
   When clicked, the presenter emits `open_request_in_isolated_tab`. The payload is a *deep copy* (`RequestData.model_copy(deep=True)`) of the request.
3. **Tab Injection:** 
   `MainWindow` routes this signal to `TabsPresenter.add_new_tab`. Because the `TabsPresenter` receives a distinct `RequestData` instance, edits made within this tab do not leak to other tabs.
4. **Restoration on Startup:** 
   When PyPost is re-opened, `TabsPresenter.restore_tabs()` iterates through previously open tab IDs. It intentionally passes deep copies of the discovered `RequestData` objects when restoring tabs, to prevent multiple tabs from binding to the same memory reference upon startup.

## Limitations & Future Work
- Standard left-click navigation has not yet been modified to force deep copies. Reusing existing tabs vs. opening isolated ones on left-click is an ongoing architectural consideration.
- If a request's title is modified, `TabsPresenter.rename_request_tabs` correctly updates the title in all open tabs matching that `id`. However, deeper metadata conflicts (e.g. one tab saving a URL, while another tab is editing it) remain unmerged, operating strictly under a "last write wins" basis.