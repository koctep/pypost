# PYPOST-405: Dev Docs

## Documentation Added
- Created `doc/dev/open_request_in_isolated_tab.md` to document the architectural pattern of cloning `RequestData` objects so tabs can isolate their editing state.

## Key Takeaways
- Explained the `open_request_in_isolated_tab` signal.
- Documented why `TabsPresenter.restore_tabs` had to be updated to yield deep copies.
- Captured known limitations about "last write wins" on saving cloned tabs and left-click behavior discrepancies.