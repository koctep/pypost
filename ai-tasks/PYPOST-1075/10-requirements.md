# PYPOST-1075: Add generate_import_copy_name Test Reaching "(4)" to Fully Rule Out Non-Strict Looping

## Goals

Verify that `generate_import_copy_name` strictly re-checks collision membership on every while loop iteration by asserting that advancing through existing suffixed names ("Copy of Dev", "Copy of Dev (2)", "Copy of Dev (3)") returns "Copy of Dev (4)".

## Background

In PYPOST-1002, `test_returns_next_numbered_copy_when_first_two_taken` was added to verify advancing from suffix=2 to suffix=3 when both are taken. While this demonstrated incrementing beyond the initial suffix, verifying the loop advancing to suffix=4 when three prior names are taken establishes proof of strict loop iteration and membership re-evaluation across multiple collisions.

## Scope

### In Scope
- Adding automated unit test coverage to `TestGenerateImportCopyName` in `tests/test_environment_import.py` asserting that `generate_import_copy_name("Dev", {"Copy of Dev", "Copy of Dev (2)", "Copy of Dev (3)"})` returns `"Copy of Dev (4)"`.

### Out of Scope
- Modifying `generate_import_copy_name` algorithm in `pypost/core/import_conflicts.py` (logic is already verified and correct).
- Altering collection import copy generation.

## Functional Requirements

1. **4th Suffix Resolution**:
   - When base name `"Dev"` has existing collisions for `{"Copy of Dev", "Copy of Dev (2)", "Copy of Dev (3)"}`, `generate_import_copy_name` must return `"Copy of Dev (4)"`.

## Non-Functional Requirements

1. **Test Hygiene**: Follow standard unit test conventions with deterministic and fast execution.

## User Scenarios

### Scenario 1: Fourth Duplicate Copy Generated
- **Given** an existing set of environment names containing `Copy of Dev`, `Copy of Dev (2)`, and `Copy of Dev (3)`.
- **When** generating an import copy name for `Dev`.
- **Then** the function returns `Copy of Dev (4)`.
