# PYPOST-1544: Code Cleanup Report

## Linter Fixes

- Fixed: `MaskBreadcrumb.pop` annotated `index` as `int`. mypy reported
  a new override error because `list.pop` takes `SupportsIndex`. The
  parameter type is now `SupportsIndex`. Call sites still use `pop()`
  with no argument, so mask results stay the same.
- `make lint` completed clean: test-lint baseline, flake8 on `pypost/`,
  and user-doc checks.

## Code Formatting

Applied formatting changes:
- [ ] Automatic code formatting
- [ ] Indentation and alignment fixes
- [ ] Line length correction

Scoped Python files were already within the 100-character limit. No
formatter was applied.

## Code Cleanup

Cleanup actions performed:
- Removed unused imports: 0
- Removed unused variables: 0
- Removed commented-out code: none present
- Removed debug prints: none present

The module docstring in `tests/test_pypost_1544_failing_repro.py` said
the source checks fail on current code. It now states that `matches`
reads breadcrumb wildcard presence and that the redact and formatter
walks push the breadcrumb. Assertions are unchanged.

## Validation Results

Validation results:
- [x] All tests passed
- [x] All tests have explicit timeout markers
- [x] No merge conflicts
- [x] Syntax is valid
- [x] Types are correct (if applicable)

## Notes

`make analyze` is not a Makefile target. Static analysis used `make lint`.
The first `make typecheck` failed with one new error on
`pypost/core/json_selector_engine.py` line 126 (`override`). After the
`SupportsIndex` annotation, `make typecheck` passed: mypy baseline OK
(175 known errors). `json_selector_engine.py` has no baseline entries.

The commanded suite was `tests/test_pypost_1544_failing_repro.py`,
`tests/test_pypost_1543_failing_repro.py`,
`tests/test_pypost_1542_failing_repro.py`,
`tests/test_pypost_1394_failing_repro.py`, and
`tests/test_pypost_1388_failing_repro.py`. Result: 5 files, 0 failed.

Timeout markers are module-level `pytestmark`:
`pytest.mark.timeout(30)` in the 1544, 1543, 1542, and 1388 modules, and
`pytest.mark.timeout(60)` in `tests/test_pypost_1394_failing_repro.py`.
No conflict markers in the scoped files.

Structured `logger.debug` events stay. The 1394 observability test asserts
`json_selector_engine_compiled` and
`json_selector_engine_redact_tree_completed`.

Selector-syntax table rows in `doc/dev/json_selector_engine.md` (lines
93-98) are longer than 100 characters. They remain as written. The
documentation lint gate covers `doc/user/` and `doc/README.md`.

`MaskBreadcrumb.append` stays. It forwards to `push` so a leftover
`append` cannot leave the wildcard count behind. Walks call `push`.
`CompiledPathSelector.raw` is assigned and unread. It stays. This task
does not change tokenization or live match behavior.

`pypost/ui/widgets/response_mask_controller.py`,
`pypost/core/sensitive_text_sanitizer.py`, and
`doc/dev/json_selector_engine.md` were not edited.
