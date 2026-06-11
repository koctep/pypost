# PYPOST-316: Dev Docs

## Updates

Verified existing documentation in `doc/dev/request_actions.md` accurately describes the
post-extraction architecture:

- `RequestSaveOrchestrator` owns save/save-as dialogs and persistence.
- `TabsPresenter` delegates and applies tab updates.
- `MainWindow` wires save signals to collections refresh only.

No content changes required — docs were updated during PYPOST-322 and remain current.

## Testing Section

Dev doc references:

- `tests/test_request_save_orchestrator.py` — orchestrator unit tests
- `tests/test_tabs_presenter.py` — save-as identity and signal regression tests

Run command documented in `doc/dev/request_actions.md` Testing section.
