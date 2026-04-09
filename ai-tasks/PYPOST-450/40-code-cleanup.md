# PYPOST-450: Code Cleanup Report

## Linter Fixes

Describe fixed linter errors and warnings:

- Fixed: `E501` in `pypost/core/template_service.py` by splitting a long
  `_VALIDATION_MESSAGES.get(...)` call across multiple lines.

## Code Formatting

Applied formatting changes:

- [ ] Automatic code formatting
- [x] Indentation and alignment fixes
- [x] Line length correction

## Code Cleanup

Cleanup actions performed:

- Removed unused imports: 0
- Removed unused variables: 0
- Removed commented-out code: none found in scoped files
- Removed debug prints: none found in scoped files

## Validation Results

Validation results:

- [x] All tests passed
- [x] No merge conflicts
- [x] Syntax is valid
- [x] Types are correct (if applicable)

## Verbosity Review Findings

List implementation areas that look too verbose and should be simplified:

- Location: `pypost/core/template_service.py` (`validate_function_expressions`)
  - Why verbose: validation performs multiple sequential checks with repeated
    `return ValidationResult.error(...)` branches that can be hard to scan.
  - Suggested simplification: extract helper methods
    (`_parse_function_call`, `_validate_args`) and use early-return helpers to
    reduce conditional depth.
- Location: `pypost/ui/widgets/mixins.py` (`resolve_text`)
  - Why verbose: nested `replace` closure mixes token parsing, hidden-key
    handling, and runtime rendering in one function.
  - Suggested simplification: split into two small static helpers:
    `_resolve_plain_variable(...)` and `_resolve_expression_token(...)`.
- Location: `pypost/ui/widgets/mixins.py` (`mouseMoveEvent`)
  - Why verbose: token resolution path checks cursor index and index-1 in-line,
    then directly handles tooltip behavior.
  - Suggested simplification: introduce `_find_hover_expression(text, index)`
    and `_show_or_hide_tooltip(event, expression)` to isolate responsibilities.

## Notes

- Scope intentionally limited to STEP 3 related files only:
  `pypost/core/template_service.py`,
  `pypost/ui/widgets/mixins.py`,
  `pypost/ui/widgets/variable_aware_widgets.py`,
  `tests/test_template_service.py`,
  `tests/test_variable_hover.py`.
- Focused pytest run shows existing `DeprecationWarning` entries from Qt
  mouse-event APIs (`globalPos()` and `pos()`). These were pre-existing and are
  not addressed in this cleanup pass to keep scope aligned with PYPOST-450.
