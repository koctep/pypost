# PYPOST-973: Developer Documentation

## Updates

- `doc/dev/testing.md` — extended the model-backed item-view teardown section
  to document collections-tree adoption of `detach_item_view_model` via
  `close_isolated_tree_actions` / `isolated_tree_actions`, and the unittest
  `addCleanup` pattern (PYPOST-973).

## Overview for maintainers

Isolated collections-tree harnesses in `tests/helpers/collections_tree.py`
must detach the view model before the `QTreeView` is destroyed. Use:

```python
from tests.helpers.collections_tree import (
    build_isolated_tree_actions,
    close_isolated_tree_actions,
)

harness = build_isolated_tree_actions([...])
self.addCleanup(close_isolated_tree_actions, harness)
```

Or the context manager:

```python
from tests.helpers.collections_tree import isolated_tree_actions

with isolated_tree_actions([...]) as harness:
    ...
```

Both paths call `tests.helpers.qt_item_view.detach_item_view_model`.

## Verification

Focused suite:

```bash
make test PYTEST_ARGS="tests/test_qt_item_view_teardown.py \
  tests/test_collection_tree_actions.py \
  tests/test_collection_tree_delete_confirmation.py \
  tests/test_collection_tree_rename_context_menu.py \
  tests/test_collection_tree_rename_delegate_e2e.py -v"
```
