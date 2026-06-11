# PYPOST-317: Developer Documentation

## Purpose

Document orchestrator-level save-as test coverage added for PYPOST-34 debt closure.

## Modified Files

| File | Change |
| ---- | ------ |
| `doc/dev/request_actions.md` | Testing section: orchestrator test table and focused run command |
| `tests/test_request_save_orchestrator.py` | Six save-as orchestrator tests with mocked dialog |

## Key Takeaways for Developers

- Mock `SaveRequestDialog` at `pypost.ui.request_save_orchestrator.SaveRequestDialog` when
  testing `RequestSaveOrchestrator.save_as_request`.
- Use `_mock_save_dialog()` in `test_request_save_orchestrator.py` for consistent dialog stubs.
- Presenter tests (`test_tabs_presenter.py`) remain the place for signal routing and tab rebinding
  assertions; orchestrator tests focus on dialog → persistence → state expansion.

Focused run:

```bash
QT_QPA_PLATFORM=offscreen python -m pytest \
  tests/test_request_save_orchestrator.py tests/test_tabs_presenter.py -k save_as -v
```
