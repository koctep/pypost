# Failing Repro (N/A): PYPOST-1043

**Task**: [PYPOST-1043](https://pypost.atlassian.net/browse/PYPOST-1043)  
**Step**: STEP 3 (Failing Repro Test)  
**Target Suites**:
- `tests/test_collection_tree_actions.py` (22 tests)
- `tests/test_collection_tree_rename_context_menu.py` (8 tests)
- `tests/test_collection_tree_delete_confirmation.py` (5 tests)
- `tests/test_collection_tree_rename_delegate_e2e.py` (4 tests via `_prepare_harness`)
- `tests/test_qt_item_view_teardown.py` (2 tests, dedicated regression proof)

---

## 1. Overview & Objective

Per [10-requirements.md](file:///home/src/ai-tasks/PYPOST-1043/10-requirements.md) and [20-architecture.md](file:///home/src/ai-tasks/PYPOST-1043/20-architecture.md), PYPOST-1043 addresses technical debt item PYPOST-973 TD-1: standardizing collection-tree test harness lifecycle management from `build_isolated_tree_actions` + `self.addCleanup(close_isolated_tree_actions, harness)` to the `isolated_tree_actions` context manager pattern (`with isolated_tree_actions(...) as harness:`).

---

## 2. N/A Rationale (No Behavioral Change)

Step 3 is designated as **N/A — no behavioral change** for the following architectural reasons:

1. **No Runtime Application Changes**: This task introduces zero modifications to production code under `pypost/`, runtime dependencies, public APIs, metrics, or log schemas.
2. **Teardown Guarantees Already Present**: Model detachment (`detach_item_view_model`) and view cleanup are already implemented in `tests/helpers/collections_tree.py` and actively invoked across all consumer tests via `addCleanup(close_isolated_tree_actions, harness)`.
3. **Ergonomic / Refactoring Scope Only**: The transition from `addCleanup` to `with isolated_tree_actions(...) as harness:` is a purely cosmetic, idiomatic refactor to reduce boilerplate and align consumer test syntax with Python best practices.
4. **Preserved Assertion Semantics**: All existing test assertions, mock inspections, signal spy verifications, and timeout boundaries remain 100% identical before and after the refactoring.

Consequently, no red automated reproduction test is applicable or required prior to Step 4.

---

## 3. Baseline Test Execution

Per repository guidelines (`AGENTS.md`), the baseline execution of all 5 target test suites was verified using the project's standard Make target:

```bash
make test PYTEST_ARGS="tests/test_collection_tree_actions.py tests/test_collection_tree_rename_context_menu.py tests/test_collection_tree_delete_confirmation.py tests/test_collection_tree_rename_delegate_e2e.py tests/test_qt_item_view_teardown.py"
```

### Baseline Execution Output (Green)

```text
INFO parallel_test_run_started workers=8 enable_coverage=False report_json= test_targets=tests/test_collection_tree_actions.py,tests/test_collection_tree_rename_context_menu.py,tests/test_collection_tree_delete_confirmation.py,tests/test_collection_tree_rename_delegate_e2e.py,tests/test_qt_item_view_teardown.py pytest_arg_count=0
[  1/5  ] tests/test_qt_item_view_teardown.py ... PASSED (1.60s)
INFO test_file_completed file=tests/test_qt_item_view_teardown.py status=passed exit_code=0 duration_seconds=1.60 progress=1/5
[  2/5  ] tests/test_collection_tree_delete_confirmation.py ... PASSED (1.61s)
INFO test_file_completed file=tests/test_collection_tree_delete_confirmation.py status=passed exit_code=0 duration_seconds=1.61 progress=2/5
[  3/5  ] tests/test_collection_tree_rename_delegate_e2e.py ... PASSED (1.62s)
INFO test_file_completed file=tests/test_collection_tree_rename_delegate_e2e.py status=passed exit_code=0 duration_seconds=1.62 progress=3/5
[  4/5  ] tests/test_collection_tree_rename_context_menu.py ... PASSED (1.63s)
INFO test_file_completed file=tests/test_collection_tree_rename_context_menu.py status=passed exit_code=0 duration_seconds=1.63 progress=4/5
[  5/5  ] tests/test_collection_tree_actions.py ... PASSED (1.68s)
INFO test_file_completed file=tests/test_collection_tree_actions.py status=passed exit_code=0 duration_seconds=1.68 progress=5/5

============================== TOP 5 SLOWEST FILES ==============================
1. tests/test_collection_tree_actions.py (1.68s)
NOTICE slowest_test_file rank=1 file=tests/test_collection_tree_actions.py duration_seconds=1.68
2. tests/test_collection_tree_rename_context_menu.py (1.63s)
NOTICE slowest_test_file rank=2 file=tests/test_collection_tree_rename_context_menu.py duration_seconds=1.63
3. tests/test_collection_tree_rename_delegate_e2e.py (1.62s)
NOTICE slowest_test_file rank=3 file=tests/test_collection_tree_rename_delegate_e2e.py duration_seconds=1.62
4. tests/test_collection_tree_delete_confirmation.py (1.61s)
NOTICE slowest_test_file rank=4 file=tests/test_collection_tree_delete_confirmation.py duration_seconds=1.61
5. tests/test_qt_item_view_teardown.py (1.60s)
NOTICE slowest_test_file rank=5 file=tests/test_qt_item_view_teardown.py duration_seconds=1.60

=================================== SUMMARY ====================================
Total Files: 5 | Passed: 5 | Failed: 0 | Skipped: 0
Wall-clock duration: 1.68s | Cumulative CPU duration: 8.14s (4.8x speedup)
INFO parallel_test_run_completed total_files=5 passed=5 failed=0 skipped=0 wall_clock_seconds=1.68 cumulative_duration_seconds=8.14 speedup=4.8
```

---

## 4. Target Call-Site Inventory

| Target Test Suite File | Call Sites | Current Pattern | Target Step 4 Pattern |
| --- | :---: | --- | --- |
| `tests/test_collection_tree_actions.py` | 22 | `harness = build_isolated_tree_actions(...)`<br/>`self.addCleanup(close_isolated_tree_actions, harness)` | `with isolated_tree_actions(...) as harness:` |
| `tests/test_collection_tree_rename_context_menu.py` | 8 | `harness = build_isolated_tree_actions(...)`<br/>`self.addCleanup(close_isolated_tree_actions, harness)` | `with isolated_tree_actions(...) as harness:` |
| `tests/test_collection_tree_delete_confirmation.py` | 5 | `harness = build_isolated_tree_actions(...)`<br/>`self.addCleanup(close_isolated_tree_actions, harness)` | `with isolated_tree_actions(...) as harness:` |
| `tests/test_collection_tree_rename_delegate_e2e.py` | 1 (`_prepare_harness`) | `harness = build_isolated_tree_actions(..., with_rename_delegate=True)`<br/>`self.addCleanup(close_isolated_tree_actions, harness)` | `with isolated_tree_actions(..., with_rename_delegate=True) as harness:` |
| `tests/test_qt_item_view_teardown.py` | 0 | Dedicated teardown tests (`test_close_isolated_tree_actions_detaches_model` & `test_isolated_tree_actions_context_manager_detaches_model`) | **Preserved intact** (no change) |

---

## 5. Strict Constraints Verification

- **Zero Production Code Changes**: No files under `pypost/` have been modified.
- **Zero Test Code Changes in Step 3**: Target test suites remain untouched in this step; changes will be applied during Step 4.
- **Make-Only Invocation**: Baseline execution verified strictly through `make test`.

---

## 6. Downstream Handoff (Step 4: Development)

In Step 4, the following migration phases will be executed sequentially:
1. **Phase A**: Refactor 22 test methods in `tests/test_collection_tree_actions.py` to `with isolated_tree_actions(...) as harness:`, removing `addCleanup` and updating imports.
2. **Phase B**: Refactor 8 test methods in `tests/test_collection_tree_rename_context_menu.py` to `with isolated_tree_actions(...) as harness:`, removing `addCleanup` and updating imports.
3. **Phase C**: Refactor 5 test methods in `tests/test_collection_tree_delete_confirmation.py` to `with isolated_tree_actions(...) as harness:`, removing `addCleanup` and updating imports.
4. **Phase D**: Refactor `tests/test_collection_tree_rename_delegate_e2e.py` to `with isolated_tree_actions(..., with_rename_delegate=True) as harness:`, removing `addCleanup` and updating imports.
5. **Phase E**: Update documentation in `doc/dev/testing.md` to reference `isolated_tree_actions` context manager pattern.
