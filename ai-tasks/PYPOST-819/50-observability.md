# PYPOST-819: Observability

## Production observability

No changes. Closing the last request tab continues to use the existing
`TabsPresenter.close_tab` path (`removeTab` → `add_new_tab` when count is zero →
`save_tabs_state`). No new logs or metrics were required for focus selection after
last-tab close.

## Test observability

The regression test asserts UI focus outcomes:

- One request tab remains after closing the last one (replacement)
- `currentIndex` is not the plus-tab index (`PLUS_TAB_MARKER` / `_plus_tab_index`)
- `widget(current)` is a `RequestTab`
- Replacement tab text is `"New Request"`

No `caplog` or metrics assertions — this is a focus/index contract, not an error path.

## Validation Results

- [x] No production logging changes required
- [x] Focus assertions document the product contract in the test docstring
- [x] Large data structures are not logged (N/A)
