# PYPOST-345: Architecture

## Baseline (after PYPOST-342)

| Layer | Module | Rename coverage |
| --- | --- | --- |
| Delegate unit | `test_collection_item_rename_delegate.py` | Editor create/setModelData/cancel callbacks |
| Isolated actions | `test_collection_tree_actions.py` | Handlers + mocked `view.edit` |
| Context menu | `test_collection_tree_rename_context_menu.py` | Menu + mocked `view.edit` + direct handlers |
| Presenter metrics | `test_collection_tree_rename_metrics.py` | Error/not_found via presenter |
| Presenter wiring | `test_collections_presenter.py` | Menu → mocked `view.edit` |

**Gap:** no test runs `QTreeView.edit` with the production delegate wired to
`CollectionTreeActions`.

## Plan

1. Extend `tests/helpers/collections_tree.py`:
   - `wire_rename_delegate(harness)` — mirror `CollectionsPresenter` delegate wiring
   - `with_rename_delegate=True` on `build_isolated_tree_actions`
   - `wait_for_rename_editor`, `commit_inline_rename`, `cancel_inline_rename` — bounded GUI helpers
2. Add `tests/test_collection_tree_rename_delegate_e2e.py`:
   - Request/collection commit → `selected` + `succeeded`
   - Request cancel → `selected` + `cancelled`
   - Request empty name → `selected` + `rejected_empty`
3. Document new module in `doc/dev/collection_tree_actions.md`.

## Test matrix (PYPOST-345 additions)

| Flow | Delegate e2e module |
| --- | --- |
| Context menu → real edit → commit (request) | yes |
| Context menu → real edit → commit (collection) | yes |
| Context menu → real edit → cancel | yes |
| Context menu → real edit → empty name | yes |
