# PYPOST-279: Code Cleanup

## Lint

```bash
.venv/bin/python -m flake8 --jobs=1 tests/test_pytest_exit_policy.py
```

Exit code 0 — no new flake8 issues.

## Format

No formatting changes required; file follows project conventions (LF, UTF-8, ≤100 chars).

## Scope

Single new test module; no production code changes.
