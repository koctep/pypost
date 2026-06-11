# PYPOST-322: Code Cleanup

## Lint and Format

- Ran targeted save tests: 13 passed.
- Removed unused `uuid` import from `tabs_presenter.py` after extraction.
- No new flake8 issues in touched modules.

## Files Touched

| File | Notes |
| ---- | ----- |
| `pypost/ui/request_save_orchestrator.py` | New module |
| `pypost/ui/presenters/tabs_presenter.py` | Delegates to orchestrator |
| `tests/test_request_save_orchestrator.py` | New unit tests |
| `tests/test_tabs_presenter.py` | Updated `SaveRequestDialog` patch target |

## Deferred

- Repository-wide flake8 baseline cleanup remains tracked under PYPOST-323.
