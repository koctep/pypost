# PYPOST-320: Developer Documentation

## Purpose

Document GUI-level integration test coverage for save and save-as flows.

## Modified Files

| File | Change |
| ---- | ------ |
| `doc/dev/request_actions.md` | Testing section adds save-flow integration tests and run command |

## Key Takeaways for Developers

- Use `tests/test_save_flow_integration.py` when changing `RequestWidget` action callbacks or
  `TabsPresenter` save signal wiring.
- Entry points under test: menu actions and keyboard shortcuts (`Ctrl+S`, `Ctrl+Shift+S`).
- Dialogs remain mocked; for orchestrator-only behavior see
  `tests/test_request_save_orchestrator.py`.
