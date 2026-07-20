# PYPOST-818: Observability

## Production observability

No changes. Closing a request tab continues to use the existing `TabsPresenter.close_tab`
path (`removeTab` + optional blank-tab ensure + `save_tabs_state`). No new logs or metrics
were required for focus selection after close.

## Test observability

The regression test asserts UI focus outcomes:

- `currentIndex` is not the plus-tab index (`PLUS_TAB_MARKER` / `_plus_tab_index`)
- `widget(current)` is a `RequestTab`

No `caplog` or metrics assertions — this is a focus/index contract, not an error path.
