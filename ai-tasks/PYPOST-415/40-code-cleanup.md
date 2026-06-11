# PYPOST-415: Code Cleanup

## Changes Reviewed

| File | Assessment |
|------|------------|
| `pypost/ui/presenters/tabs_presenter.py` | Worker cleanup extracted; UI reset simplified |
| `tests/test_worker_race.py` | New test follows existing presenter mock pattern |

## Cleanup Actions

- Removed `tab.worker = None` from `_reset_tab_ui_state` (single-responsibility).
- Consolidated duplicate stale cleanup inline block into `_clear_tab_worker`.
- Docstring on `_clear_tab_worker` documents Qt queued-signal gap (no stray comments elsewhere).

## Static Analysis

No new linter issues introduced in modified files.

## Test Run

```
pytest tests/test_worker_race.py -v
```

All 4 tests expected to pass (3 existing + 1 new).
