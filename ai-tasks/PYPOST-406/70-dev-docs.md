# PYPOST-406: Dev Docs

## Documentation Updated

- Updated `doc/dev/open_request_in_isolated_tab.md` to reflect unified deep-copy behavior for
  left-click, context-menu **New tab**, and `TabsPresenter.add_new_tab`.

## Key Changes Documented

- Left-click on a Collections request now emits a deep copy (same contract as **New tab**).
- `TabsPresenter.add_new_tab` always deep-copies non-`None` `request_data` before constructing
  `RequestTab` — canonical enforcement for all tab-open callers.
- Removed the prior limitation that left-click could share one `RequestData` reference across
  tabs.
- Troubleshooting table updated: cross-tab edit leakage should no longer occur for tree opens.

## Related Artifacts

- Requirements: `ai-tasks/PYPOST-406/10-requirements.md`
- Architecture: `ai-tasks/PYPOST-406/20-architecture.md`
