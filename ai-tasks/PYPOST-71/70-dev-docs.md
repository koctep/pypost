# PYPOST-71 — Dev Docs

## Updates

| Doc | Change |
|-----|--------|
| `doc/dev/request_execution.md` | Document explicit tab binding at `send_requested` wire time |

## Key Point

`TabsPresenter._wire_tab_signals` captures the `RequestTab` in a closure when connecting
`send_requested`. `_handle_send_request(sender_tab, request_data)` no longer calls
`QObject.sender()`, so the handler is safe to invoke directly (e.g. in tests) without a
Qt signal context.

## Test Reference

- `tests/test_tabs_presenter.py::TestTabsPresenterSendRequestTabBinding::test_handle_send_request_accepts_explicit_tab_without_sender`
