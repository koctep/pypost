# PYPOST-996: Code Cleanup

## Cleanup Actions

- Ported retry loop and scratch cleanup to `check-lock-dev` and `check-lock-otel` in `Makefile`.
- Parametrized `tests/test_makefile_check_lock_retry.py` across all three targets.
- Verified flake8 and pytest test suites — all clean.
