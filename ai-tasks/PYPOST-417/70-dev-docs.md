# PYPOST-417 — Dev Docs

## Updated

- `doc/dev/request_execution.md` — new subsection **One-shot worker instances (PYPOST-417)**

## Content added

- `_stop_event` is set only by `stop()` and never cleared after init
- Reusing a stopped worker silently cancels requests
- `TabsPresenter` contract: new worker per send; `_clear_tab_worker` on completion

## Cross-references

- PYPOST-401 — stop flag race fixes
- PYPOST-415 — tab worker cleanup
- `tests/test_worker_race.py::test_worker_not_reusable_after_stop`
