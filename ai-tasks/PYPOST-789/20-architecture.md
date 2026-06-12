# PYPOST-789: [Bug] make test fails: 7 regression tests (SOLID caps + theme isolation)

## Research

The 7 failures were mapped to two distinct root causes:
1. `test_solid_audit_baseline.py` failed due to normal LOC growth in `MainWindow` and `template_service.py` exceeding outdated static caps.
2. `test_style_manager_theme.py` failed due to stylesheet pollution from other GUI tests, forcing the returned style to be wrapped in a nameless `QStyleSheetStyle` subclass.

## Implementation Plan

1. Adjust caps in `scripts/audit_baseline_metrics.py` (PYPOST-717).
2. Isolate `test_style_manager_theme.py` using a state backup/restoration module fixture (PYPOST-722).
3. Run `make test` to verify both are resolved.

## Architecture

This is a coordination bug that resolves test environment issues. No direct architectural alterations are made here; we rely on the specific architectures of the subtasks.

## Q&A

- **Q**: Are there any other failures in `make test`?
- **A**: No, the rest of the 1416 tests are passing successfully.
