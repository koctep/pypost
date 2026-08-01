# PYPOST-941: Architecture

## Overview

Extract the recursive DisplayRole walk from `ui_actions._find_tree_index_by_text`
into a shared production module; delegate both call sites.

## Current State

| Location | Walk | Error on miss |
| --- | --- | --- |
| `ui_actions._find_tree_index_by_text` | Recursive model index, DisplayRole | `UiTargetNotInteractableError` (via `_select_tree`) |
| `agent_e2e_tree.find_tree_index_by_text` | Depth-2 `QStandardItem` text only | `AssertionError` |

## Decision

| Choice | Rationale |
| --- | --- |
| Module `pypost/agent/tree_index.py` | Production + tests import; no test→prod inversion |
| Return `QModelIndex \| None` | Callers map to agent vs assertion errors |
| Keep thin wrappers | Preserve public error types at each boundary |

## Step 3 Failing Repro Plan

1. Add `tests/test_tree_index_walk.py`:
   - Build 3-level `QTreeView` fixture.
   - `find_tree_index_by_text(tree, "Grandchild")` must succeed (fails today:
     e2e helper only scans two levels).
   - Assert miss raises `AssertionError`, not `UiTargetNotInteractableError`.
2. Expected red: `AssertionError: tree row not found: text='Grandchild'`.

## Step 4 Implementation

1. Create `find_tree_index_by_display_text` in `pypost/agent/tree_index.py`.
2. Replace `_find_tree_index_by_text` in `ui_actions.py` with import + delegate.
3. Rewrite `agent_e2e_tree.find_tree_index_by_text` to delegate; keep
   `AssertionError` message.
4. Run `tests/test_tree_index_walk.py`, `tests/test_ui_actions.py`, and
   agent e2e modules that import `click_tree_row_by_text`.

## Verification

```bash
make test PYTEST_ARGS='tests/test_tree_index_walk.py tests/test_ui_actions.py -v'
```
