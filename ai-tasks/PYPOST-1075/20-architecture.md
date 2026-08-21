# PYPOST-1075: Add generate_import_copy_name Test Reaching "(4)" to Fully Rule Out Non-Strict Looping

## Research

### Existing Test Suite Analysis
In `tests/test_environment_import.py`, `TestGenerateImportCopyName` currently tests:
- `test_returns_copy_of_name_when_free` (base free case -> `"Copy of Dev"`)
- `test_returns_numbered_copy_when_first_taken` (first taken -> `"Copy of Dev (2)"`)
- `test_returns_next_numbered_copy_when_first_two_taken` (first two taken -> `"Copy of Dev (3)"`)

### Architectural Plan
Extend `TestGenerateImportCopyName` in `tests/test_environment_import.py` by adding:
`test_returns_next_numbered_copy_when_first_three_taken`:
- Given `existing_names = {"Copy of Dev", "Copy of Dev (2)", "Copy of Dev (3)"}`
- When calling `generate_import_copy_name("Dev", existing_names)`
- Assert result equals `"Copy of Dev (4)"`

## Implementation Plan

1. **Step 3 (Failing Repro)**:
   - Add `test_returns_next_numbered_copy_when_first_three_taken` to `TestGenerateImportCopyName` in `tests/test_environment_import.py`.
   - Run pytest and verify pass.
2. **Step 4 (Development)**:
   - Verify green test suite execution.
3. **Step 5-8**:
   - Code cleanup, observability review, tech-debt recording, and dev doc updates in `doc/dev/environments_dialog.md`.

## Architecture

```text
generate_import_copy_name("Dev", {"Copy of Dev", "Copy of Dev (2)", "Copy of Dev (3)"})
  │
  ├─ format_copy_of_name("Dev") ──> "Copy of Dev" (in set -> proceed)
  ├─ suffix = 2 ──> "Copy of Dev (2)" (in set -> suffix = 3)
  ├─ suffix = 3 ──> "Copy of Dev (3)" (in set -> suffix = 4)
  └─ suffix = 4 ──> "Copy of Dev (4)" (not in set -> return)
```

### Components
- `pypost.core.import_conflicts.generate_import_copy_name`
- `tests.test_environment_import.TestGenerateImportCopyName`

## Q&A

### Q1: Is production code changed?
**A:** No. `generate_import_copy_name` already handles infinite iterative loops correctly. This test validates multi-step loop iteration up to suffix 4.
