# PYPOST-252: Code Cleanup

## Lint

```bash
.venv/bin/python -m flake8 --jobs=1 \
  tests/test_request_manager.py \
  tests/test_request_manager_delete.py \
  tests/test_settings_persistence.py
```

Result: no new issues.

## Tests

Focused manager suite:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_request_manager.py \
  tests/test_request_manager_delete.py \
  tests/test_settings_persistence.py::TestStateManagerPersistence \
  tests/test_settings_persistence.py::test_state_manager_debounced_save_persists_after_timer \
  -v --cov=pypost.core.request_manager --cov=pypost.core.state_manager --cov-report=term-missing
```

Result: 37 passed; RequestManager 100% line coverage; StateManager 98% (one defensive early
return in `_on_debounced_save_timeout` when pending flag already cleared).

Full suite:

```bash
make test
```

## Formatting

No formatting changes required; existing file style preserved.
