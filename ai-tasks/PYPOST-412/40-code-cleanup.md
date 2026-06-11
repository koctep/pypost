# PYPOST-412: Code Cleanup

## Scope

Single-file production change in `pypost/core/worker.py`; test update in `tests/test_worker.py`.

## Changes reviewed

| File | Action |
|------|--------|
| `pypost/core/worker.py` | Removed 3-line dead `except ExecutionError` block |
| `tests/test_worker.py` | Replaced mock-raise test with `ExecutionResult` contract test |

## Lint / format

- No new imports added; `ExecutionError` import retained (retry callback + Exception wrapper).
- Line length within 100 characters.
- Trailing whitespace: none.

## Verification

```bash
python -m unittest tests.test_worker -v
```

All worker tests pass.
