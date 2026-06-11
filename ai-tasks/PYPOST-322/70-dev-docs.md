# PYPOST-322: Developer Documentation

## Purpose

Document the extracted save orchestrator and updated architecture references.

## Modified Files

| File | Change |
| ---- | ------ |
| `doc/dev/request_actions.md` | Architecture section references `RequestSaveOrchestrator` |
| `ai-tasks/PYPOST-322/70-dev-docs.md` | This summary |

## Key Takeaways for Developers

- Save persistence logic lives in `pypost/ui/request_save_orchestrator.py`.
- `TabsPresenter` calls `RequestSaveOrchestrator.save_request` / `save_as_request` and applies
  tab-specific UI updates from the returned `SaveResult`.
- Unit tests: `tests/test_request_save_orchestrator.py` (orchestrator) and existing presenter
  save-as tests (integration through presenter).
