# PYPOST-349: Technical Debt Analysis

## Shortcuts Taken

- **Callback injection over QObject signals**: `CollectionTreeActions` uses injected
  callables rather than defining its own signals. Simpler for a refactor but slightly
  more wiring in `CollectionsPresenter.__init__`.

## Code Quality Issues

- **Presenter still exposes private delegates** (`_show_context_menu`, `_handle_delete`,
  `_on_editor_closed`, `_pending_rename`) for test compatibility. Could be trimmed when
  tests target `CollectionTreeActions` directly.
- **Rename/delete still share QMessageBox patterns** with other UI areas (PYPOST-344
  remains open).

## Missing Tests

- No dedicated unit tests for `CollectionTreeActions` in isolation; coverage relies on
  existing `test_collections_presenter.py` delegation paths.

## Performance Concerns

None introduced. Incremental rename/delete tree updates (PYPOST-347) unchanged.

## Follow-up Tasks

- Add direct unit tests for `CollectionTreeActions` (menu dispatch, rename cancel/commit).
- Consolidate QMessageBox error/confirmation helpers across UI (PYPOST-344).
