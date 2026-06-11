# PYPOST-461: Code Cleanup Report

## Linter Fixes

- Ran `./scripts/lint.sh` on `tests/test_function_expression_resolver.py`: **E402** on
  imports after `pytestmark` — **pre-existing** pattern shared with other test modules; no
  change required for this ticket.
- No new flake8 findings introduced by PYPOST-461 additions.

## Code Formatting

Applied formatting changes:

- [ ] Automatic code formatting (no `black`/`ruff` in repo scripts)
- [x] Indentation and alignment fixes (none required)
- [x] Line length correction (`./scripts/check-line-length.sh` on scoped files;
      all lines ≤ 100 characters)

## Code Cleanup

Cleanup actions performed:

- Removed unused imports: **0**
- Removed unused variables: **0**
- Removed commented-out code: **none**
- Removed debug prints: **none**
- Added module-level case constants (`EMPTY_ARGUMENT_CASES`,
  `STANDALONE_MALFORMED_CLOSING_PAREN_CASES`, `MULTI_PLACEHOLDER_FIRST_FAILURE_CASES`)
  following PYPOST-454 `MALFORMED_NESTED_EXPRESSION_CASES` precedent.

## Validation Results

Validation results:

- [x] Scoped tests passed (`tests/test_function_expression_resolver.py`,
      `tests/test_template_service.py`, `tests/test_http_client.py`: **109 passed**, 51
      subtests)
- [x] All new tests have explicit timeout via module `pytestmark = pytest.mark.timeout(30)`
- [x] No merge conflicts
- [x] Syntax is valid

**Note:** Full `make test` hit a pre-existing Qt/PySide6 segfault on Python 3.14 in this
environment after ~60s. Expression-related suites pass cleanly; no regression attributable to
PYPOST-461 changes.

## Notes

- Tests-only delivery; no production files modified.
- Case constants are resolver-scoped only (not imported by `test_template_service.py`) because
  first-failure and empty-arg behavior are resolver contract tests without render-parity
  requirements.
