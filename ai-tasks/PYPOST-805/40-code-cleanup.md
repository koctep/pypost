# PYPOST-805: Code Cleanup Report

## Linter Fixes

No application code changes; no linter fixes required.

## Code Formatting

Applied formatting changes:

- [x] Makefile target reduced to single scan command (no inline pip install)
- [x] CI job step split for clarity (app deps → dev tooling → audit)
- [x] Line length within 100 characters

## Code Cleanup

Cleanup actions performed:

- Removed duplicate scanner install paths (Makefile + CI) in favor of dev lock
- Kept `security-audit: install` prerequisite so local scan matches CI install graph
- Updated `pyproject.toml` dev extra to satisfy PYPOST-785 drift test

## Validation Results

Validation results:

- [x] All tests passed (`make check`)
- [x] `make security-audit` passes
- [x] `make check-lock-dev` passes (lock regenerated)
- [x] All tests have explicit timeout markers (no new tests added)

## Notes

No changes to `tests/test_makefile.py` — `test_security_audit_depends_on_install` remains valid;
`install` now implicitly provides `pip-audit` through `venv-test`.
