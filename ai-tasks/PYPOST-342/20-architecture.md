# PYPOST-342: Architecture

## Baseline

Delete-flow GUI coverage already uses a three-layer pattern:

| Layer | Module | Role |
| --- | --- | --- |
| Helpers | `tests/helpers/collections_tree.py` | Fake managers, QMenu patches |
| Isolated actions | `test_collection_tree_delete_confirmation.py` | Menu dispatch + metric sequences |
| Presenter metrics | `test_collection_tree_delete_metrics.py` | Error/not_found via `CollectionsPresenter` |

Rename had unit tests in `test_collection_tree_actions.py` and presenter callback tests in
`test_collections_presenter.py`, but lacked parallel GUI/metrics modules.

## Plan

1. Add `patch_rename_context_menu` mirroring `patch_delete_context_menu`.
2. Add `test_collection_tree_rename_context_menu.py` for isolated rename menu dispatch and
   lifecycle metric assertions (`selected` through `succeeded` / `rejected_empty`).
3. Add `test_collection_tree_rename_metrics.py` for presenter-level error and not-found paths
   (same shape as delete metrics tests).
4. Extend `test_collections_presenter.py` with context-menu rename → inline edit wiring.
5. Document new modules in `doc/dev/collection_tree_actions.md`.

## Test matrix

| Status | Isolated context menu | Presenter metrics |
| --- | --- | --- |
| `selected` | yes | via presenter context-menu tests |
| `cancelled` | yes | yes |
| `succeeded` | yes | existing presenter rename tests |
| `rejected_empty` | yes | yes |
| `error` | — | yes |
| `not_found` | — | yes |
