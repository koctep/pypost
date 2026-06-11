# PYPOST-414: Dev Docs

## Changes

- `doc/dev/testing.md` — added focused regression command for PYPOST-400/PYPOST-403 test
  surface.

## Verification commands

```bash
# PYPOST-400 worker/error-handling + deferred test fixes
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_http_client_sse_probe.py \
  tests/test_history_manager.py \
  tests/test_worker.py \
  tests/test_retry.py \
  tests/test_tabs_presenter.py::TestOnRequestError \
  -v --tb=short

# Full suite
make test
```

## Key patterns for future tests

1. **HTTPClient in tests** — always pass `template_service=TemplateService()` (or rely on
   production default after PYPOST-403).
2. **HistoryManager with temp dirs** — call `hm.flush()` before exiting
   `TemporaryDirectory` when `append`/`delete`/`clear` triggered async save.

## Cross-references

- PYPOST-403 `70-dev-docs.md` — detailed fix narrative
- PYPOST-400 `60-review.md` — original TD-6 filing
