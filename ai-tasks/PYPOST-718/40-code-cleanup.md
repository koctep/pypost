# PYPOST-718: Code Cleanup

## Static analysis

- `read_lints` on `tests/test_makefile.py`, `tests/test_pytest_exit_policy.py` — no issues.

## Formatting

- Line length ≤ 100 characters maintained.

## Cleanup actions

| Item | Action |
| ---- | ------ |
| Unused imports | None added |
| Dead code | None |
| Debug output | None |
| Test timeouts | Module timeouts unchanged |

## Test run

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_makefile.py tests/test_pytest_exit_policy.py -q
```

All tests pass (see commit verification).
