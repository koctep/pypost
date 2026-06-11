# PYPOST-326: Code Cleanup

- Removed unused delegation methods from `CollectionsPresenter`:
  `_show_context_menu`, `_handle_delete`, `_on_editor_closed`.
- Updated tests to call `presenter._tree_actions` APIs directly.
- No lint issues in touched files.
