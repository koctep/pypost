# Step 3 Failing Repro: Strengthen DisplayRole Ownership AST

**Task**: [PYPOST-1041](https://pypost.atlassian.net/browse/PYPOST-1041)  
**Step**: STEP 3 (Failing Repro Test)  
**Target Test File**: `tests/test_display_role_scan_ownership.py`  
**Repro Test File**: `tests/test_display_role_scan_ownership_repro.py`  

---

## 1. Overview & Objective

Per [20-architecture.md](file:///home/src/ai-tasks/PYPOST-1041/20-architecture.md), Step 3 introduces automated red tests that demonstrate the architectural and coverage gaps in `tests/test_display_role_scan_ownership.py` *before* applying strengthening changes in Step 4.

The target file `tests/test_display_role_scan_ownership.py` currently asserts:
- Function definitions for `display_role_equals` and `find_child_index_by_display_text` exist in `tree_index.py`.
- `find_tree_index_by_display_text` delegates to `display_role_equals` and does not access `ItemDataRole.DisplayRole` inline.
- `_select_item_view` in `ui_actions.py` delegates to `find_child_index_by_display_text` and does not access `ItemDataRole.DisplayRole` inline.

However, it currently **fails to check**:
1. That `find_child_index_by_display_text` delegates to `display_role_equals`.
2. That `find_child_index_by_display_text` does not inline `ItemDataRole.DisplayRole`.
3. That `pypost.agent.tree_index.__all__` explicitly exports `display_role_equals`, `find_child_index_by_display_text`, and `find_tree_index_by_display_text`.
4. Mutation resistance: an AST mutant of `tree_index.py` where `find_child_index_by_display_text` inlines `ItemDataRole.DisplayRole` or where `__all__` is emptied goes undetected by the current ownership test suite.

---

## 2. Test Execution Command

Executed strictly via Make per repository guidelines (`AGENTS.md`):

```bash
make test PYTEST_ARGS="tests/test_display_role_scan_ownership_repro.py"
```

---

## 3. Repro Test Results

### Summary

```text
tests/test_display_role_scan_ownership_repro.py::test_repro_ownership_suite_checks_find_child_delegation FAILED [1ms] [ 20%]
tests/test_display_role_scan_ownership_repro.py::test_repro_ownership_suite_checks_find_child_forbids_inline_display_role FAILED [1ms] [ 40%]
tests/test_display_role_scan_ownership_repro.py::test_repro_ownership_suite_checks_tree_index_all_exports FAILED [1ms] [ 60%]
tests/test_display_role_scan_ownership_repro.py::test_repro_ownership_suite_catches_inlined_display_role_mutant FAILED [2ms] [ 80%]
tests/test_display_role_scan_ownership_repro.py::test_repro_ownership_suite_catches_empty_all_exports_mutant FAILED [2ms] [100%]

============================== 5 failed in 0.09s ===============================
```

### Detailed Failure Traces

#### 1. `test_repro_ownership_suite_checks_find_child_delegation`
- **Assertion**: `tests/test_display_role_scan_ownership.py` must contain an AST check that `find_child_index_by_display_text` calls `display_role_equals`.
- **Traceback**:
  ```text
  tests/test_display_role_scan_ownership_repro.py:157: in test_repro_ownership_suite_checks_find_child_delegation
      assert _has_find_child_delegation_check(tree), (
  E   AssertionError: tests/test_display_role_scan_ownership.py must assert that find_child_index_by_display_text calls display_role_equals
  E   assert False
  E    +  where False = _has_find_child_delegation_check(<ast.Module object at 0xe7f24118a950>)
  ```

#### 2. `test_repro_ownership_suite_checks_find_child_forbids_inline_display_role`
- **Assertion**: `tests/test_display_role_scan_ownership.py` must contain an AST check that `find_child_index_by_display_text` does not reference `ItemDataRole.DisplayRole`.
- **Traceback**:
  ```text
  tests/test_display_role_scan_ownership_repro.py:166: in test_repro_ownership_suite_checks_find_child_forbids_inline_display_role
      assert _has_find_child_forbids_display_role_check(tree), (
  E   AssertionError: tests/test_display_role_scan_ownership.py must assert that find_child_index_by_display_text does not access ItemDataRole.DisplayRole inline
  E   assert False
  E    +  where False = _has_find_child_forbids_display_role_check(<ast.Module object at 0xe7f24100ffd0>)
  ```

#### 3. `test_repro_ownership_suite_checks_tree_index_all_exports`
- **Assertion**: `tests/test_display_role_scan_ownership.py` must verify `__all__` in `pypost.agent.tree_index` exports `display_role_equals` and `find_child_index_by_display_text`.
- **Traceback**:
  ```text
  tests/test_display_role_scan_ownership_repro.py:175: in test_repro_ownership_suite_checks_tree_index_all_exports
      assert _has_all_exports_check(tree), (
  E   AssertionError: tests/test_display_role_scan_ownership.py must verify that pypost.agent.tree_index.__all__ exports display_role_equals and find_child_index_by_display_text
  E   assert False
  E    +  where False = _has_all_exports_check(<ast.Module object at 0xe7f24102bfd0>)
  ```

#### 4. `test_repro_ownership_suite_catches_inlined_display_role_mutant`
- **Assertion**: Running the ownership test against a mutated `tree_index.py` (where `find_child_index_by_display_text` inlines `ItemDataRole.DisplayRole`) must raise an `AssertionError`.
- **Result**: Fails because the current unstrengthened test suite fails to detect the mutation.
- **Traceback**:
  ```text
  tests/test_display_role_scan_ownership_repro.py:194: in test_repro_ownership_suite_catches_inlined_display_role_mutant
      with pytest.raises(
  E   Failed: DID NOT RAISE <class 'AssertionError'>
  ```

#### 5. `test_repro_ownership_suite_catches_empty_all_exports_mutant`
- **Assertion**: Running the ownership test against a mutated `tree_index.py` (where `__all__` is empty) must raise an `AssertionError`.
- **Result**: Fails because the current unstrengthened test suite does not inspect `__all__`.
- **Traceback**:
  ```text
  tests/test_display_role_scan_ownership_repro.py:214: in test_repro_ownership_suite_catches_empty_all_exports_mutant
      with pytest.raises(
  E   Failed: DID NOT RAISE <class 'AssertionError'>
  ```

---

## 4. Failure Mode Analysis

| Failure Mode | Reason | Expected Resolution in Step 4 |
| --- | --- | --- |
| Missing delegation check | `test_display_role_scan_ownership.py` does not assert `_calls_name(find_child, "display_role_equals")` | Add assertion in `test_flat_and_tree_share_display_role_match_helper` |
| Missing inline DisplayRole prohibition | `test_display_role_scan_ownership.py` does not assert `not _has_display_role_attr(find_child)` | Add assertion in `test_flat_and_tree_share_display_role_match_helper` |
| Missing `__all__` export validation | `test_display_role_scan_ownership.py` lacks helper and assertions for `tree_index.__all__` | Add `_module_all_exports` helper and assert `expected_exports.issubset(tree_exports)` |
| Mutation undetected | The unstrengthened test suite passes even when `find_child_index_by_display_text` inlines `DisplayRole` | Strengthened assertions will catch the mutant and raise `AssertionError` |

---

## 5. Strict Constraints Verification

- **No Production Code Changes**: No files under `pypost/` were modified.
- **No Target Test Premature Edits**: `tests/test_display_role_scan_ownership.py` remains untouched at this step.
- **Hermetic & Bounded**: All tests use explicit `@pytest.mark.timeout(10)` per `do-testing` guidelines and execute in < 100ms with zero network or GUI dependencies.
