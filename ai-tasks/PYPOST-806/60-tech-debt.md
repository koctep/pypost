# PYPOST-806: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

## Shortcuts Taken

- Lock files (`requirements*.txt`) remain alongside `pyproject.toml`; direct pins are duplicated
  and guarded by `tests/test_pyproject.py` (manual sync on dependency changes).
- Editable install resolves direct pins from `pyproject.toml`; transitive versions may differ
  from compiled locks until a unified lock strategy lands.
- `security-audit` CI no longer pre-installs production packages; scan remains file-based on
  `requirements.txt`.

## Code Quality Issues

None blocking. Makefile and CI changes follow PYPOST-785 optional-extra conventions.

## Missing Tests

- No dedicated test asserts `pip install -e ".[dev]"` package discovery beyond Makefile smoke
  (slow test covers full `pyproject.toml` editable install).
- No test verifies transitive pin parity between editable install and `requirements.txt` lock.

## Performance Concerns

None. Editable install may resolve fewer redundant pip steps in `make install` (single command vs
three lock-file installs).

## Follow-up Tasks

None. Inherited debt from PYPOST-785/PYPOST-779 (production `check-lock` CI, pytest config
migration PYPOST-807) is unchanged and out of scope.
