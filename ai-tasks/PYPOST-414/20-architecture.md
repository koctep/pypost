# PYPOST-414: Architecture

## Context

Fixes were implemented in PYPOST-403 (`afd2a58`). PYPOST-414 verifies closure of the
PYPOST-400 debt item without duplicating production changes.

## Failure → fix mapping

| Failure | Root cause | Fix (PYPOST-403) |
|---------|------------|------------------|
| SSE probe `AttributeError` | `_template_service` was `None` | `HTTPClient` default-constructs `TemplateService()`; tests inject in `setUp` |
| History `OSError` on tmpdir exit | Daemon save thread still writing | `HistoryManager.flush()` joins `_save_thread`; tests call `flush()` before context exit |

## Components (unchanged in PYPOST-414)

```
tests/test_http_client_sse_probe.py
    └── HTTPClient(template_service=TemplateService())  # setUp

tests/test_history_manager.py
    └── hm.append(...) → hm.flush()  # before TemporaryDirectory exit

pypost/core/http_client.py
    └── __init__: self._template_service = template_service or TemplateService()

pypost/core/history_manager.py
    └── flush(): join pending _save_thread
```

## PYPOST-400 regression surface

Worker/error-handling paths validated separately:

- `pypost/core/worker.py` → `tests/test_worker.py`
- `pypost/core/request_service.py` → `tests/test_retry.py`
- `pypost/ui/presenters/tabs_presenter.py` → `tests/test_tabs_presenter.py::TestOnRequestError`

## Decision

No new architecture for PYPOST-414 — verification and documentation only.
