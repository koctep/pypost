# PYPOST-344: Code Cleanup

- Removed direct `QMessageBox` import from `collection_tree_actions.py`.
- Dialog titles (`Rename Error`, `Delete Error`, `Confirm Delete`) centralized in
  `collection_item_dialogs.py`.
- Test patches updated to mock helpers at the `collection_tree_actions` import site.
