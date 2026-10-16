# PYPOST-1414: Developer Documentation

## Overview

PYPOST-1414 enhances the workspace environment variable import capability introduced in PYPOST-1411
by adding a 9-column side-by-side diff inspector, per-variable conflict strategy resolution, bulk
strategy actions, and dual-source secret masking.

This developer documentation records all architecture, API, UI, and test documentation updates made
across the codebase to support maintainers, developers, and testers.

---

## Documentation Updates

### 1. Developer Guide: [`doc/dev/workspace_environment_variable_import.md`](../../doc/dev/workspace_environment_variable_import.md)

The developer guide was comprehensively updated with the following enhancements:

- **Overview & Architectural Decomposition**:
  - Referenced child task [PYPOST-1414](https://pypost.atlassian.net/browse/PYPOST-1414) alongside PYPOST-1411 under epic [PYPOST-1407](https://pypost.atlassian.net/browse/PYPOST-1407).
  - Updated architectural layer summary to highlight side-by-side comparison, per-variable strategy resolution, bulk actions, and dual-source secret masking.
  - Updated Mermaid component architecture diagram to reflect domain engine support for per-variable conflict policies.

- **Domain Engine API & Precedence**:
  - Updated function signature for `import_collection_variables_to_environment`:
    ```python
    def import_collection_variables_to_environment(
        environment: Environment,
        collection: Collection,
        conflict_strategy: ConflictStrategy = ConflictStrategy.SKIP,
        selected_keys: set[str] | None = None,
        preset_name: str | None = None,
        variable_conflict_strategies: dict[str, ConflictStrategy] | None = None,
    ) -> ImportSummary:
    ```
  - Documented `variable_conflict_strategies: dict[str, ConflictStrategy] | None`: an optional mapping of variable name to specific `ConflictStrategy` (`SKIP` or `OVERWRITE`).
  - Documented the exact resolution precedence:
    1. *Explicit Per-Variable Strategy*: If `variable_conflict_strategies` contains the colliding key, its explicit strategy is honored.
    2. *Default Strategy Fallback*: If not present in `variable_conflict_strategies` (or if `None`), falls back to `conflict_strategy` (defaults to `ConflictStrategy.SKIP`).
    3. *Non-Colliding Variables*: Variables not currently in `environment.variables` are imported as new variables regardless of conflict strategy settings.

- **Dual-Source Secret Masking**:
  - Documented dual-source masking rules: values in both the **Current Value** and **Candidate Value** columns in `ImportCollectionVariablesDialog` are masked with `HIDDEN_MASK` (`"********"`) if the variable is marked secret in either the source collection (`var.secret is True`) or the target destination environment (`var.name in environment.hidden_keys`).
  - Documented that plaintext secrets are never exposed in comparison tables or structured log events.

- **UI Layer: 9-Column Side-by-Side Diff Inspector (`ImportCollectionVariablesDialog`)**:
  - Documented table layout with columns `[Select, Name, Current Value, Candidate Value, Conflict Strategy, Type, Secret, Status, Description]` (`IMPORT_COLLECTION_VARS_TABLE`).
  - Documented per-row conflict resolution: interactive `QComboBox` (`IMPORT_COLLECTION_ROW_STRATEGY_COMBO_PREFIX<key>`) embedded for colliding rows defaulting safely to `"Keep Current"` (`ConflictStrategy.SKIP`) vs `"Overwrite"` (`ConflictStrategy.OVERWRITE`), and non-interactive dash (`"—"`) for non-colliding rows.
  - Documented bulk collision controls: `"Keep All Collisions"` (`IMPORT_COLLECTION_BULK_KEEP_CURRENT_BUTTON`) and `"Overwrite All Collisions"` (`IMPORT_COLLECTION_BULK_OVERWRITE_BUTTON`).
  - Documented dynamic preview summary recalculation (`"{will_add} new to add, {will_overwrite} existing to overwrite, {will_keep} existing to keep"`).
  - Documented preservation of per-row strategy choices across preset profile switches.

- **Structured Observability**:
  - Added new log events:
    - `collection_variable_import_table_populated` (DEBUG): total variables and collision counts.
    - `collection_variable_import_row_strategy_changed` (DEBUG): variable key and chosen strategy.
    - `collection_variable_import_bulk_strategy_applied` (INFO): applied bulk strategy and affected count.
    - `collection_variable_import_dialog_accepted` (INFO): detailed collision breakdown (`collisions`, `overwrite_collisions`, `keep_collisions`).

- **Troubleshooting & FAQ**:
  - Updated troubleshooting advice regarding colliding variable preservation (`Keep Current` default), changing per-row combo boxes, and using bulk actions.
  - Clarified secret masking behavior across side-by-side comparison columns.

- **Testing Documentation**:
  - Added reference to `tests/test_workspace_environment_import_diff_repro.py` detailing domain engine tests, 9-column UI table layout, per-row combo selection, bulk collision buttons, dual-source masking, and strategy persistence.

---

## Files Modified

| File | Change Description |
| --- | --- |
| `doc/dev/workspace_environment_variable_import.md` | Comprehensive updates for PYPOST-1414 (API, architecture, 9-column UI diff table, per-row combo, bulk buttons, dual-source masking, observability, testing). |
| `ai-tasks/PYPOST-1414/00-roadmap.md` | Marked Step 8 as `[/]` with sub-items and documented artifacts. |
| `ai-tasks/PYPOST-1414/70-dev-docs.md` | Created Step 8 developer documentation summary artifact. |

---

## Verification

All operations must be run exclusively via `make` targets:

```bash
# Run linting (flake8 static analysis and markdown doc linting)
make lint

# Run AI task artifact validation
make verify-ai-tasks

# Run the repro test suite
make test PYTEST_ARGS="tests/test_workspace_environment_import_diff_repro.py"

# Run the combined quality check
make check
```
