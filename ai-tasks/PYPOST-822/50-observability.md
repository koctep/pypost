# PYPOST-822: Observability

## Production observability

No changes. Next/previous tab switching continues to use the existing
`TabsPresenter.handle_next_tab` / `handle_previous_tab` path (navigable indices only).
No new logs or metrics were required for hotkey focus selection.

## Test observability

The regression test asserts UI focus outcomes after hotkey-map activation:

- Registered shortcuts match product keys (`Ctrl+Tab`, `Ctrl+Shift+Tab`)
- After next and previous activations (including wrap), `currentIndex` is not the plus-tab
  index and `widget(current)` is a `RequestTab`

No `caplog` or metrics assertions — this is a focus/index contract, not an error path.
