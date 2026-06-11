# PYPOST-321: Code Cleanup

## Lint and Format

- No production code changes; test-only diff.
- Ran targeted test module; no new flake8 issues in edited file.

## Review Checklist

- [x] Test name describes regression invariant.
- [x] Uses existing `FakeRequestManager` and dialog mock pattern from sibling tests.
- [x] No duplicate coverage of signal-only behavior (complements existing save-as signal test).
