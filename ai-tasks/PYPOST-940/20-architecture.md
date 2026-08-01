# PYPOST-940: Architecture

## Overview

Add `tests/helpers/qt_item_view.py` with two functions:

| Function | Role |
| --- | --- |
| `detach_item_view_model(view)` | Call `setModel(None)` when a model is attached |
| `close_item_view_fixture(root, qapp, widget_id, *, view_type=...)` | Find widget by id, detach model, close root, pump events |

## Design

- **Location:** `tests/helpers/qt_item_view.py` alongside `collections_tree.py`
  and other Qt test utilities.
- **Consumers:** Replace `_close_tree_fixture` and `_close_list_view_fixture`
  in `tests/test_ui_actions.py` with calls to `close_item_view_fixture`,
  passing `QTreeView` or `QListView` as `view_type` for isinstance checks.
- **No production changes** — test-only module.

## Step 3 Failing Repro Plan

1. Add `tests/test_qt_item_view_teardown.py` with:
   - Import of `detach_item_view_model` and `close_item_view_fixture` from
     `tests.helpers.qt_item_view` (fails: module missing).
   - Behavioral test: after `detach_item_view_model`, `view.model()` is `None`.
2. Expected red failure: `ModuleNotFoundError: tests.helpers.qt_item_view`.

## Step 4 Implementation

1. Create `tests/helpers/qt_item_view.py`.
2. Refactor `test_ui_actions.py` teardown to use `close_item_view_fixture`.
3. Remove duplicate private `_close_*` helpers.
4. Run `tests/test_qt_item_view_teardown.py` and `tests/test_ui_actions.py`.

## Verification

```bash
make test PYTEST_ARGS="tests/test_qt_item_view_teardown.py tests/test_ui_actions.py -v"
```

No Qt warnings on item-view select tests when run with `-W default`.
