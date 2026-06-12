# PYPOST-162 — Dev Docs

## Updates

| Doc | Change |
|-----|--------|
| `doc/dev/request_execution.md` | Document explicit tab binding for save/save-as; note `_create_request_tab` factory |

## Key Point

`TabsPresenter._create_request_tab` is the single production path for new request tabs. It
calls `_wire_tab_signals`, which captures the `RequestTab` in closures for send, save, and
save-as. Handlers accept `source_tab` explicitly and do not call `QObject.sender()`.

## Test Reference

- `tests/test_tabs_presenter.py::TestTabsPresenterSaveTabBinding::test_handle_save_request_accepts_explicit_tab_without_sender`
