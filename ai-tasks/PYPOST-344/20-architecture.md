# PYPOST-344: Architecture

## Design

Introduce `pypost/ui/collection_item_dialogs.py` as a thin presentation helper module.
`CollectionTreeActions` imports helpers instead of calling `QMessageBox` inline.

```mermaid
flowchart LR
    CTA[CollectionTreeActions]
    CID[collection_item_dialogs]
    QB[QMessageBox]
    CTA --> CID --> QB
```

| Helper | Replaces |
|--------|----------|
| `confirm_delete(parent, item_label)` | Delete Yes/No question |
| `show_rename_empty_name_error(parent)` | Empty rename warning |
| `show_rename_failure(parent, label, error)` | Rename exception critical |
| `show_rename_not_found(parent, label)` | Rename not-found warning |
| `show_delete_failure(parent, label, error)` | Delete exception critical |
| `show_delete_not_found(parent, label)` | Delete not-found warning |

## Implementation plan

1. Add `collection_item_dialogs.py` with the six helpers above.
2. Replace inline `QMessageBox` calls in `collection_tree_actions.py`.
3. Update tests to patch helpers at the `collection_tree_actions` import site.
4. Add unit tests for dialog helper behavior in `test_collection_item_dialogs.py`.

## Out of scope

- Tabs, environment, history, and settings QMessageBox usage.
- Changing dialog copy or adding new user-facing messages.
