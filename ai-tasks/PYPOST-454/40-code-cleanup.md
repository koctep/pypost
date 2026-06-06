# PYPOST-454: Code Cleanup Report

## Linter Fixes

- Ran `./scripts/lint.sh` on `tests/test_function_expression_resolver.py` and
  `tests/test_template_service.py`: **no flake8 findings** (exit 0).
- No linter-driven code edits were required beyond deduplication refactor.

## Code Formatting

Applied formatting changes:

- [ ] Automatic code formatting (no `black`/`ruff` in repo scripts)
- [x] Indentation and alignment fixes (none required in scoped files)
- [x] Line length correction (`./scripts/check-line-length.sh` on both scoped files;
      all lines ≤ 100 characters)

## Code Cleanup

Cleanup actions performed:

- Removed unused imports: **0** (none found in scoped files)
- Removed unused variables: **0**
- Removed commented-out code: **none** in scoped files
- Removed debug prints: **none** in scoped files
- **Deduplicated** M1–M4 malformed nested case tuples: extracted
  `MALFORMED_NESTED_EXPRESSION_CASES` module constant in
  `tests/test_function_expression_resolver.py`; imported by
  `tests/test_template_service.py` for `test_runtime_hover_parity_malformed_nested`
  and `test_validate_malformed_nested_alignment` (replaces three inline copies).

## Validation Results

Validation results:

- [x] All tests passed (`./scripts/test.sh tests/test_function_expression_resolver.py
      tests/test_template_service.py`: **55 passed**, 37 subtests passed)
- [x] No merge conflict markers in scoped test files
- [x] Syntax is valid
- [x] Types are correct (if applicable) — scoped Python matches existing patterns

Command outcomes:

- `./scripts/lint.sh` (two scoped files) → exit 0
- `./scripts/check-line-length.sh` (two scoped files) → exit 0
- `./scripts/test.sh tests/test_function_expression_resolver.py
  tests/test_template_service.py` → exit 0

## Verbosity Review Findings

- Location: `tests/test_function_expression_resolver.py` — `MALFORMED_NESTED_EXPRESSION_CASES`
  - Why verbose: Four-tuple rows carry label, content, code, and `function_name` for resolver
    assertions; template parity tests only need label + content.
  - Suggested simplification: **keep as-is**; `for label, content, *_ in ...` is minimal and
    preserves a single source of truth for locked observed codes.

- Location: `tests/test_function_expression_resolver.py` — `test_nested_spacing_variants`
  - Why verbose: Valid (S1–S3) and invalid (S4–S5) spacing rows are inline; S4–S5 content also
    appears in `test_runtime_hover_parity_invalid_spacing` without shared validation tuples.
  - Suggested simplification: **keep as-is** for PYPOST-454; spacing invalid rows differ in
    assertion shape (resolver checks codes; integration checks render fallback only). Optional
    follow-up: extract `SPACING_VARIANT_CASES` if more rows are added.

- Location: `tests/test_template_service.py` — `test_runtime_hover_parity_valid_spaced_nested`
  - Why verbose: S1–S3 content strings overlap resolver spacing matrix but include per-path
    expected hash values for render parity.
  - Suggested simplification: **keep as-is**; expected hashes are integration-specific and should
    not be folded into resolver-only constants.

No other material verbosity in scoped files.

## Notes

- Scoped lint and tests are the authoritative checks for this task; project-wide flake8 may
  report pre-existing issues in unrelated modules.
- No production code (`pypost/core/`) changes in this step.
- Importing a test-data constant from `tests.test_function_expression_resolver` follows the
  minimal scoped-file approach; project `tests/helpers.py` is reserved for reusable fakes/mocks
  (e.g. `FakeStorageManager`), not expression matrices.
