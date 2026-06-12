# PYPOST-179: Code Cleanup (Step 4)

## Lint

```bash
make lint
```

- No new flake8 issues in `pypost/fixtures/` or `scripts/generate_mcp_test_fixtures.py`.

## Tests

```bash
.venv/bin/python -m pytest tests/test_generate_mcp_test_fixtures.py \
  tests/test_mcp_test_collection.py -v
```

- All targeted tests pass.

## Formatting

- UTF-8, LF line endings, trailing newline on generated JSON and Python sources.
- Line length within 100 characters.
