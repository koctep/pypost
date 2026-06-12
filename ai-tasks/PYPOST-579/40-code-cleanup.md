# PYPOST-579: Code Cleanup (Step 4)

## Lint

```bash
make lint
```

- No new flake8 issues in `pypost/core/metrics_otel.py` or `tests/test_metrics_otel.py`.

## Tests

```bash
.venv/bin/python -m pytest tests/test_metrics_otel.py tests/test_metrics_protocol.py -v
```

- All targeted tests pass.

## Formatting

- UTF-8, LF line endings, trailing newline on Python sources.
- Line length within 100 characters.
