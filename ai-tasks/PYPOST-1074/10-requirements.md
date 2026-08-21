# PYPOST-1074: Extend 3+-Conflict Apply-to-All Test Matrix to OVERWRITE/KEEP_BOTH Decisions

## Goals

Ensure complete test-matrix coverage for bulk conflict resolution when importing environment files with three or more naming collisions. Verify that choosing "Apply to all remaining conflicts" with `OVERWRITE` or `KEEP_BOTH` decisions correctly propagates to all subsequent conflicts beyond the first two.

## Background

In PYPOST-1002, `test_apply_to_all_conflicts_applies_to_third_and_later_conflicts` was added to verify the `SKIP` decision when importing 3 colliding environments. However, the test matrix lacked test cases asserting the behavior of `OVERWRITE` and `KEEP_BOTH` across 3+ conflicts:
- `OVERWRITE` should update all conflicting existing environments in place, preserving existing environment IDs and updating their variable payloads.
- `KEEP_BOTH` should retain existing environments and create numbered duplicate copies (e.g., "Dev (1)", "Prod (1)", "Staging (1)") for all conflicting entries.

## Scope

### In Scope
- Adding automated unit test coverage to `TestImportEnvironments` in `tests/test_environment_list_widget.py` for:
  1. `OVERWRITE` decision applied to 3+ conflicts with "Apply to all" enabled.
  2. `KEEP_BOTH` decision applied to 3+ conflicts with "Apply to all" enabled.
- Asserting the exact resulting environments, variables, and IDs after import completion.

### Out of Scope
- Modifying UI dialog layouts or business logic in `EnvironmentListWidget`.
- Changing collection import conflict resolution.

## Functional Requirements

1. **3+ Conflict OVERWRITE Propagation**:
   - When 3 existing environments ("Dev", "Prod", "Staging") collide with 3 incoming records, and the user selects `OVERWRITE` with "Apply to all remaining conflicts" checked:
   - The user must only be prompted once.
   - All 3 environments must have their variables updated to the incoming values.
   - All 3 existing environment IDs must remain intact.
2. **3+ Conflict KEEP_BOTH Propagation**:
   - When 3 existing environments collide with 3 incoming records, and the user selects `KEEP_BOTH` with "Apply to all remaining conflicts" checked:
   - The user must only be prompted once.
   - The existing 3 environments must remain unchanged.
   - 3 new environments with suffixed copy names ("Dev (1)", "Prod (1)", "Staging (1)") must be created and added to the list.

## Non-Functional Requirements

1. **Test Hygiene**: All tests must include explicit timeouts (`pytestmark = pytest.mark.timeout(...)`), follow clean setup/teardown patterns, and execute synchronously without race conditions.

## User Scenarios

### Scenario 1: Apply to All with OVERWRITE on 3 Conflicts
- **Given** 3 existing environments: Dev, Prod, Staging.
- **When** importing a file containing Dev, Prod, Staging with updated variables, and selecting OVERWRITE with "Apply to all".
- **Then** all 3 environments are overwritten in-place without prompting again.

### Scenario 2: Apply to All with KEEP_BOTH on 3 Conflicts
- **Given** 3 existing environments: Dev, Prod, Staging.
- **When** importing a file containing Dev, Prod, Staging, and selecting KEEP_BOTH with "Apply to all".
- **Then** 3 new renamed environments are appended alongside the existing ones without prompting again.
